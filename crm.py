#crm.py

customers = []

def crm():
    def welcome_message():
        print("Hello! And welcome to the business CRM 1.0")
    welcome_message()
    while True:
        options = input("1.add customer 2. print customers or enter + blank to end the program ")
        if options == "":
            break
        elif options == "1":
                add_customer()        
        elif options == "2":
                print(customers)

def add_customer():      
    name = input("name of your customer: ")
    email = input("email of your customer: ")
    customer = {"name": name, "email": email }
    customers.append(customer)

    print(f"{customer} has been added to your database.")
    print(f"Updated db") 

if __name__ == "__main__":
    crm()