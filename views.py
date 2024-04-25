from django.shortcuts import render, redirect  # Add redirect if needed
from .forms import PaymentForm
from .models import Payment ,Order, Subscription
import requests
import json
import os
from dotenv import load_dotenv
from django.http import HttpResponseBadRequest
from django.http import JsonResponse


def payment_form(request):
    load_dotenv()
    headers = {
                "Content-Type": "application/json",
                "X-AccountNo": os.environ.get('AccountNo'),
                "X-SecretKey": os.environ.get('SecretKey') 
                        }
    response = requests.post('https://api.sandbox.payzaty.com/checkout',  data=json.dumps(payload), headers=headers)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            order = form.save()
         

            # Construct Payzaty API request payload
            payload = {
                "merchant_id":os.environ.get('AccountNo'), 
                "api_key":os.environ.get('SecretKey'), 
                "order_id": order.order_id,
                "amount": order.amount, 
                "payment_methods": [method.name for method in order.payment_methods.all()],
                "card_types": [card.name for card in order.card_types.all()],
                "currency":order.currency,
                "language":order.language,
                "reference":order.reference,
                "customer": {
                    "name":order.customer.name,
                    "email":order.customer.email,
                    "phone":order.customerphone,
                },
                "bank_code":order.bank_code,
                "benificiary_name":order.benificiary_name,
                "iban_number":order.iban_number,
                "amount": order.amount,
                "value_date":order.value_date,
                "tokenization": True,
                "response_url":order.response_url,
                "cancel_url":order.cancel_url,
                # ... Other required parameters per Payzaty's documentation 
            }

            # Send request to Payzaty
            response = requests.post('https://api.sandbox.payzaty.com',data=json.dumps(payload))

            # Handle Payzaty's response
       
    # Handle Payzaty's response
    if response.status_code == 200:
        payment_data = response.json()
        # Redirect to Payzaty's checkout page
        return redirect(payment_data['checkout_url'])  

    elif response.status_code == 401: 
        # Authentication Failed
        return render(request, 'payment_error.html', context={'error_message': 'Authentication failed. Please check your merchant ID and API key.'})

    elif response.status_code == 403:  
        # Forbidden
        return render(request, 'payment_error.html', context={'error_message': 'The requested service might not be activated. Please contact Payzaty support.'})

    elif response.status_code == 422:
        error_data = response.json()
        # Handle specific validation errors if you want to provide more targeted messages
        return render(request, 'payment_error.html', context={'error_message': f"Invalid data: {error_data['error_text']}"})

    else:  
        # Catch-all for unexpected errors
        return render(request, 'payment_error.html', context={'error_message': 'An unexpected error occurred with Payzaty. Please try again later.'})
import requests

def get_checkout_details(checkout_id):
    base_url = "https://api.sandbox.payzaty.com"  # Update if production URL is different
    endpoint = f"/checkout/{checkout_id}"
    url = base_url + endpoint

    headers = {
        "Content-Type": "application/json",
        "X-AccountNo": os.environ.get('PAYZATY_MERCHANT_ID'),
        "X-SecretKey": os.environ.get('PAYZATY_API_KEY') 
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        checkout_data = response.json()
        return checkout_data['status']  # Assuming 'status' exists in the response
  
    elif response.status_code == 401:
        return "Authentication Failed"  # Or raise a specific AuthenticationError 
    
    elif response.status_code == 404:
        return "Checkout Not Found"  # Or raise a CheckoutNotFoundError
    
    else:
        return "Unexpected Error"  # Replace with more specific handling later
def check_payment_status(request):
    checkout_id = request.GET.get('checkout_id')# ... Retrieve the stored checkout_id 
    result = get_checkout_details(checkout_id)
    

    if isinstance(result, str):  # Indicates an error occurred
        if result == "Authentication Failed":
            return render(request, 'payment_error.html', context={'error_message': 'Authentication failed. Please check your merchant ID and API key.'})

        elif result == "Checkout Not Found":
            return render(request, 'payment_error.html', context={'error_message': 'Invalid checkout ID.'}) 

        else:  # Unexpected error
            return render(request, 'payment_error.html', context={'error_message': 'An unexpected error occurred with Payzaty. Please try again later.'})
    else:
        checkout_data = result  # Assuming 'result' is the parsed JSON
        status = checkout_data.get('status', 'Unknown') 

        if status == "Paid":
            order = Order.objects.get(heckout_id=checkout_id)  
            order.status = 'paid'
            order.save()
            return render(request, 'payment_success.html') 

        elif status == "Pending":
            return render(request, 'payment_pending.html') 

        elif status == "Failed":
            # Handle payment failure, potentially updating order status
            return render(request, 'payment_error.html', context={'error_message': 'Payment failed.'})  

        else:  
            return render(request, 'payment_error.html', context={'error_message': 'Unknown payment status.'}) 

def process_subscription_payment(subscription_id):
    # ... Call the /subscription/{subscription_id}/pay endpoint 

    response = requests.post(...)  
    if response.status_code == 200:
        payload = response.json()
        if payload.get('status') == "Captured":  # Or the exact text they use
            subscription = Subscription.objects.get(pk=subscription_id)
            order = Order.objects.create(
                subscription=subscription,
                amount=payload['amount'],
                # ... other order details
            )
            # ... success logic, emails etc.
        else:  # 'Not Captured' or other unexpected status
            # ... Handle potential issues with the subscription payment
            pass  # Add error handling or retry logic here 

    elif response.status_code == 401:
        # Handle authentication errors
        pass
    elif response.status_code == 404:
        # Handle invalid subscription ID 
        pass
    elif response.status_code == 422:
        # Handle invalid input data 
        pass
    elif response.status_code == 403:
        # Handle forbidden (unsubscribed)
        pass
    else:
        # Handle other unexpected server errors
        pass  
 
def subscribe_view(request):
    
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            plan = form.cleaned_data['plan']
            card_token = get_card_token(request.POST)  # Implement tokenization securely
            # ... Call Payzaty's subscription creation API 
            # ... Create Subscription object
            return redirect('subscription_success') 
    else:
        form = SubscriptionForm()
    return render(request, 'subscribe.html', {'form': form})
def process_payment(request):
    if request.method != 'POST': 
        return HttpResponseBadRequest("Invalid request method.")  # Good practice

    payload = request.POST  
    if 'card_token' in payload:  # Assuming you get the token as 'card_token'
        payload['payment_method'] = "Token"

    try:
        card_token = payload['card_token']  # Ensure the 'card_token' key exists
    except KeyError:
        return HttpResponseBadRequest("Missing card token in payload.")

    # ... Construct the rest of your payload ...

    response = requests.post("https://api.sandbox.payzaty.com/checkout/pay", json=payload, headers=headers)

    if response.status_code == 200:
        checkout_data = response.json()
        if 'authentication_url' in checkout_data:
            return redirect(checkout_data['authentication_url']) 
        else:
            # Handle other success/failure cases (more on this below) 
            return render(request, 'payment_result.html', context={'payment_status': checkout_data})  # Example

    elif response.status_code == 401:
        return render(request, 'payment_error.html', context={'error_message': 'Authentication failed. Please check your merchant ID and API key.'})

    elif response.status_code == 404:
        return render(request, 'payment_error.html', context={'error_message': 'Invalid token.'})

    elif response.status_code == 422:
        error_data = response.json()
        return render(request, 'payment_error.html', context={'error_message': f"Invalid data: {error_data.get('error_text')}"})

    elif response.status_code == 403:
        return render(request, 'payment_error.html', context={'error_message': 'The requested service might not be activated. Please contact Payzaty support.'})

    else:  
        return render(request, 'payment_error.html', context={'error_message': 'An unexpected error occurred with Payzaty. Please try again later.'})
from django.http import HttpResponseBadRequest, HttpResponseNotFound  # Import for error handling

def cancel_subscription(request, subscription_id): 
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method.") 

    # ... (Authentication/authorization logic if applicable) ... 

    try:
        subscription = Subscription.objects.get(pk=subscription_id)
    except Subscription.DoesNotExist:
         return HttpResponseNotFound("Subscription does not exist.")

    # Construct the request to Payzaty's cancel endpoint
    cancel_url = f"https://api.sandbox.payzaty.com/subscription/{subscription_id}/cancel"
    response = requests.post(cancel_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get('success') == True:  # Check Payzaty's success indicator
            subscription.status = 'canceled' 
            subscription.save()
            return render(request, 'subscription_cancelled.html')  # Success!
        else:
            # Handle the case where Payzaty reports an error despite a 200 status
            return render(request, 'subscription_error.html', context={'error_message': 'An error occurred while cancelling the subscription.'})

    elif response.status_code == 400:
        error_data = response.json()
        if error_data.get('error_text') == "The subscription is already cancelled":
            # Display a message that the subscription was already cancelled
            return render(request, 'subscription_already_cancelled.html') 
        else:
            return render(request, 'subscription_error.html', context={'error_message': f"Invalid data: {error_data.get('error_text')}"})

    # ... Handle other error codes (401, etc.)

def full_refund(request, checkout_id):
    # ... (Authentication/authorization logic if applicable) ... 
    refund_url = f"https://api.sandbox.payzaty.com/checkout/{checkout_id}/refund"
    response = requests.post(refund_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get('success') == True: 
            # Update your Order status for the refunded checkout_id
            return render(request, 'refund_success.html')  # Success!
        else:
            return render(request, 'refund_error.html', context={'error_message': data.get('msg', 'An unknown error occurred during the refund process.')})
    elif response.status_code == 401:
        # Handle authentication errors
        pass
    elif response.status_code == 404:
        # Handle the case where the checkout ID is not found 
        pass 
    else: 
        # Handle unexpected error codes 
        pass

def partial_refund(request, checkout_id):
     # ... (Authentication/authorization logic if applicable) ... 
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method.") 

    payload = request.POST 
    refund_url = f"https://api.sandbox.payzaty.com/checkout/{checkout_id}/refund/partial"
    response = requests.post(refund_url, json=payload,  headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get('success') == True: 
            # Update your Order status for the refunded checkout_id
            return render(request, 'refund_success.html')  # Success!
        else:
            return render(request, 'refund_error.html', context={'error_message': data.get('msg', 'An unknown error occurred during the refund process.')})
    elif response.status_code == 401:
        # Handle authentication errors
        pass
    elif response.status_code == 404:
        # Handle the case where the checkout ID is not found 
        pass 
    else: 
        # Handle unexpected error codes 
        pass
from django.http import JsonResponse  # For returning JSON responses

def check_card(request, bin):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method.") 

    # Construct the request to Payzaty's check card endpoint
    check_url = f"https://api.sandbox.payzaty.com/card/check/{bin}"
    response = requests.post(check_url, headers=headers)

    if response.status_code == 200:
        return JsonResponse(response.json())  # Return Payzaty's response directly
    elif response.status_code == 401:
        return JsonResponse({'error': 'Authentication failed'}, status=401) 
    elif response.status_code == 422:
        return JsonResponse(response.json(), status=422) 
    else:
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
    