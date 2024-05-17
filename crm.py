#crm.py

customers = []

def crm():
    #Welcoming the user
    def welcome_message():
        print("Hello! And welcome to the Business CRM 1.0")
    welcome_message()
    
    while True:
        options = input("Enter an option: 1.Add a customer 2. Print customer list (Press ENTER without any option to end the program ")
        if options == "":
            #Politely thanking the user for using the software at the end of the session
            print("Thank you for using the Business CRM 1.0")
            break
        elif options == "1":
            add_customer()        
        elif options == "2":
            print_customers()

#The function to handle the logic with adding of a new customer
def add_customer():      
    name = input("name of your customer: ")
    email = input("email of your customer: ")
    customer = {"name": name, "email": email }
    customers.append(customer)

    print(f"{customer} has been added to your database.")
    print(f"Updated database") 

def print_customers():
    if customers:
        print("Customers list:")
        for customer in customers:
            print(f"Name: {customer['name']}, Email: {customer['email']}")
    else:
        print("No customers in the database.")


if __name__ == "__main__":
    crm()