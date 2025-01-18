import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
#importing firebase libraries
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate(r'src\FirebaseKey.json')
firebase_admin.initialize_app(cred)


db = firestore.client()





# URL base for FRED series
url_base = "https://fred.stlouisfed.org/series/DGS"

def get_rf(years):
    # Construct the complete URL based on the input
    series_url = f"{url_base}{years}"

    # Make the request to the FRED website
    response = requests.get(series_url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the specific <span> element with the class attribute
        specific_span = soup.find('span', class_='series-meta-observation-value')

        if specific_span:
            # Extract and print the text content of the specific <span>
           # print(f"Data for {years} years: {specific_span.text}")

            if years == 1:
                print("Year one")
                #upload to database
                yr1 = specific_span.text

                data= {
                    'price1':yr1
                }

                doc_ref = db.collection('price').document('price1')
                doc_ref.set(data)

                print("DOCmentID",doc_ref.id)



            if years == 2:
                print("Year two")
                print(specific_span)
                #upload to database
                yr2 = specific_span.text

                data2= {
                    'price2':yr2
                }

                doc_ref = db.collection('price').document('price2')
                doc_ref.set(data2)

                print("DOCmentID",doc_ref.id)

            if years == 3:
                print("Year three")
                print(specific_span)
                #upload to database
                yr3 = specific_span.text

                data3= {
                    'price3':yr3
                }

                doc_ref = db.collection('price').document('price3')
                doc_ref.set(data3)

                print("DOCmentID",doc_ref.id)
                #upload to database   

            if years == 5:
                print("Year five")
                print(specific_span)
                #upload to database
                print(specific_span)
                #upload to database
                yr5 = specific_span.text

                data5= {
                    'price5':yr5
                }

                doc_ref = db.collection('price').document('price5')
                doc_ref.set(data5)

                print("DOCmentID",doc_ref.id)

            if years == 10:
                print("Year ten")
                print(specific_span)
                print(specific_span)
                #upload to database
                yr10 = specific_span.text

                data10= {
                    'price10':yr10
                }

                doc_ref = db.collection('price').document('price10')
                doc_ref.set(data10)

                print("DOCmentID",doc_ref.id) 

                print("Successfully uploaded data to Firebase")               
                #upload to database


        else:
            print(f"The specified <span> for {years} years was not found on the page.")
    else:
        print(f'Failed to retrieve the web page for {years} years.')

while True:
    # Get data for years 1, 2, 3, 5, and 10
    for years in [1, 2, 3, 5, 10]:
        get_rf(years)

        # Wait for an hour before the next iteration
    time.sleep(3600)  # 3600 seconds = 1 hour
    



