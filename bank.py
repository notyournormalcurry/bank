import logging
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float
from sqlalchemy import insert, update, select, and_

class Customer:
    """
    class Customer: bank customers 
    class variable: _customerSequence, increments by 1 for each new customer
    properties: cid, fn, ln 
    methods: isNew()
    """
    #private customer number, initialize to 1
    _customerSequence = 1

    def __init__(self, firstname, lastname):
        self.fn = firstname
        self.ln = lastname
        self.cid = 0 
        #call isNew() to add/find this cutomer from database
        self.isNew()

    #if this is a new Customer, add to table cutomer
    def isNew(self):
        global db

        if self.cid != 0:
            return False 
        #look up the Customer table
        self.cid = db.findCustomer(self)
        if self.cid != 0:
            return False 
        else:
            self.cid = self._customerSequence
            self._customerSequence += 1
            db.addCustomer(self)
            return True 

class BankAccount:
    """
    class BankAccount: base class
    class variable: _accountN, increment 1 for each added account
    properties: balance 
    methods: addAccount(), deposit(), withdraw();
    """
    #class variable, static variable
    _accountN = 0   #private account sequence number

    def __init__(self, cid=None):
        self.cid = cid 
        self.balance = 0 

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance):
        self._balance = new_balance

    def addAccount(self, atype = 'checking'):
        BankAccount._accountN += 1
        #lg.debug(f'static variable {BankAccounte._accountN}')
        self.aid = BankAccount._accountN
        db.addAccount(self.aid, self.cid, atype)

    def deposit(self, amount):
        global db 

        if amount <= 0:
            raise ValueError("Deposit amount below 0")
        self.balance += amount
        print('deposit: ', amount, 'balance: ', self.balance)
        db.updateBalance(self.aid, self.balance)
    
    def withdraw(self, amount):
        global db 

        if amount > self.balance:
            raise ValueError("Withdraw amount exceeded balance")
        self.balance -= amount
        db.updateBalance(self.aid, self.balance)
    
class CheckingAcount(BankAccount):
    """
    class CheckingAccount: 
    class attribut: limit, the maximum amount can be withdrawn each time
    properties: 
    methods: openAccount(), withdraw();
    """
    limit = 1000

    def __init__(self, cid=None):
        super().__init__(cid)
        self.type = "checking"
        #find if this cid has an account
        self.aid, bal = db.findAccount(cid, self.type)
        if self.aid != 0:
            BankAccount.balance=bal

    def openAccount(self):
        global db

        if self.aid != 0:
            return      #do nothing, already have an account
        super().addAccount('checking')

    def withdraw(self, amount):
        if amount > self.limit:
            raise ValueError("Withdraw amount exceeded limit")
        super().withdraw(amount)

class SavingAccount(BankAccount):
    """
    class SavingAccount:
    properties: 
    methods: openAccount(), interest()
    """

    def __init__(self, cid=None):
        super().__init__(cid)
        self.type = "saving"
        #find if this cid has an account
        self.aid, bal = db.findAccount(cid, self.type)
        if self.aid != 0:
            BankAccount.balance=bal

    def openAccount(self):
        if self.aid != 0:
            return      #do nothing, already have an account
        super().addAccount('saving')

    def interest(self):
        #here to define a way to calculate the interest
        return 100

class Database:
    """
    class Database: create and access database
    properties: engine, connection 
    methods: findCustomer(), addCustomer(), findAccount(), addAccount(),
             updateBalance(), close() 
    """
    def __init__(self, name):
        #connect to database, create if not exist
        lg.debug("Connect to database: "+name)
        self.engine = create_engine(name)
        self.connection = self.engine.connect()
        metadata = MetaData()
        tbs = self.engine.table_names()
        lg.debug(tbs)
        #create table: customer
        self.customer = Table('customer', metadata,
            Column('id', Integer(), unique=True),
            Column('firstName', String(255), nullable=False),
            Column('lastName', String(255), nullable=False))
        if 'customer' not in tbs: 
            lg.debug("Create table: customer")
            metadata.create_all(self.engine)
        self.account = Table('account', metadata,
                Column('id', Integer(), unique=True),
                Column('customerId', Integer()),
                Column('type', String(255), nullable=False),
                Column('balance', Float(), default=0))
        if 'account' not in tbs:
            lg.debug("Create table: account")
            metadata.create_all(self.engine)

    #search the cutomer firstName and lastname in the cutomer
    #table, return cutomer id if found, otherwise return 0
    def findCustomer(self, cust):
        stmt = select([self.customer])
        stmt = stmt.where( 
            and_(self.customer.columns.firstName == cust.fn,
                 self.customer.columns.lastName == cust.ln))
        result = self.connection.execute(stmt).fetchall()
        if len(result) != 1:
            return 0
        return result[0].id    #return the cutomer ID

    def addCustomer(self, cust):
        #insert one row
        stmt = insert(self.customer).values(id=cust.cid,
            firstName=cust.fn,
            lastName=cust.ln)
        result = self.connection.execute(stmt)
        lg.debug(result.rowcount)

    #search the account table, return account id and balance if found, otherwise 0
    def findAccount(self, cid, type):
        stmt = select([self.account])
        stmt = stmt.where(self.account.columns.customerId == cid )
        results = self.connection.execute(stmt).fetchall()
        lg.debug('findAccount')
        lg.debug(results)
        for acnt in results:
            if acnt.type == type:
                return acnt.id, acnt.balance    #return account Id
        return 0,0

    #create an account of type 
    def addAccount(self, aid, cid, atype='checking'):
        #insert one row
        print('addAccount: ', aid, cid, atype)
        stmt = insert(self.account).values(id=aid,
            customerId=cid,
            type=atype,
            balance=0)
        result = self.connection.execute(stmt)
        lg.debug(result.rowcount)

    def updateBalance(self, aid, bal=0):
        stmt = update(self.account)
        stmt = stmt.where(self.account.columns.id == aid )
        stmt = stmt.values(balance = bal)
        result = self.connection.execute(stmt)
        lg.debug('update balance')
        lg.debug(result.rowcount)

    #close database connection
    def close(self):
        self.connection.close()
        self.engine.dispose()

"""
 main entry point
"""
if __name__ == '__main__':
    #lg is global variable
    logging.basicConfig(level=logging.DEBUG)
    lg = logging.getLogger()

    lg.debug('logging debug')
    lg.warning('logging warning')
    lg.error('logging error')
    lg.critical('logging critical')
    #db is global variable, connect to the database
    db = Database('sqlite:///bank.sqlite')

    print('Enter your first name:')
    fn = input()
    print('Enter your last name:')
    ln = input()
    #search or create a record in customer table
    cust = Customer(fn.upper(), ln.upper())
    acntChecking = CheckingAcount(cust.cid) 
    acntSaving = SavingAccount(cust.cid)
    #loop for Main Menu
    while True:
        print('Main Menu:')
        print('Enter 0 to exit:')
        print('      1 for Checking Account:')
        print('      2 for Savings Account:')
        checking = input()
        if checking == '0':
            print('Good Bye')
            break
        if checking not in ('1', '2'):
            continue
        #loop for Sub Menu
        while True:
            print('Enter 0 for Main Menu:')
            print('      1 for balance:')
            print('      2 to withdraw:')
            print('      3 to deposit:')
            print('      4 to open new account:')
            menu = input()
            if menu == '0':
                break   
            if menu not in ('1', '2', '3', '4'):
                continue

            if checking == '1':
                acnt = acntChecking 
            else:
                acnt = acntSaving 

            if menu == '4':
                acnt.openAccount()
                continue
            #at this point, if there is no account, loop back
            if acnt.aid == 0:
                print('No Account, please open an account') 
                continue
            if menu == '1':
                bal= acnt.balance
                print('Account Balance: ', bal) 
            elif menu == '2':
                print('Enter the amount to withdraw:')
                amount = float(input())
                acnt.withdraw(amount)
            else: 
                print('Enter the amount to deposit:')
                amount = float(input())
                acnt.deposit(amount)
    #disconnect database and exit the program
    db.close()
