import json
from pymongo import MongoClient
import configparser
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


def init_order(self):
    return self["Init"]


class lt_db(object):
    def __init__(self, config):

        # connection information for DB

        self.user = config["user"]
        self.password = config["pass"]
        self.host = config["host"]
        self.port = config["port"]
        self.dbname = config["dbname"]
        self.twilsid = config["accountsid"]
        self.twilauth = config["authtoken"]

    def connect(self):
        connection = {
            f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        }
        try:
            self.client = MongoClient(connection)
            print("Connected to db!")
            return True
        except Exception as ex:
            print(f"An error occured connecting to the database.{ex}")

    def db_init(self):
        self.db = self.client.dbname
        return True

    def register_number(self, Name, ID, phoneNumber):
        """
        Register a phone number to your discord ID for use with Twilio API and verify the number through the twilio rest API.
        """
        self.db.users
        ID = str(ID)

        user = {"Name": Name, "ID": (ID), "phoneNumber": phoneNumber}
        self.db.users.insert_one(user).inserted_id

        print(f"{phoneNumber} has been added for {Name}.")

    def update_number(self, Name, ID, phoneNumber):
        """
        Update an existing number.
        """
        self.db.users
        ID = str(ID)
        query = {"ID": ID}

        user = {"Name": Name, "ID": ID, "phoneNumber": phoneNumber}
        self.db.users.replace_one(query, user)

    def get_number(self, ID):
        self.db.users
        ID = str(ID)
        query = {"ID": ID}
        numbers = []

        try:
            numbers = self.db.users.find_one(query)
        except:
            numbers = []

        return numbers

    def remove_number(self, ID):
        self.db.users
        query = {"ID": ID}

        self.db.users.delete_one(query)

    def is_valid(self, phoneNumber):
        client = Client(self.twilsid, self.twilauth)
        try:
            response = client.lookups.phone_numbers(phoneNumber).fetch(
                country_code="US"
            )
            print(f"Country code = {response.country_code}")
            return True
        except TwilioRestException as oops:
            if oops.code == 20404:
                return False
            else:
                raise oops

    def init_add(self, Guild, Category, Name, ID, Init):
        ID = str(ID)
        Guild = str(Guild)
        Category = str(Category)
        self.db[str(Guild)][str(Category)]
        Entry = {"Name": Name, "ID": ID, "Init": Init}

        self.db[str(Guild)][str(Category)].insert_one(Entry).inserted_id

    def init_clear(self, Guild, Category):

        self.db[str(Guild)][str(Category)].drop()
        self.db[str(Guild)].find_one_and_update(
            {"Category": Category}, {"$unset": {"turn": 1}}
        )

    def init_remove(self, Guild, Category, Name):
        query = {"Name": Name}

        self.db[str(Guild)][str(Category)].delete_one(query)

    def init_get(self, Guild, Category):
        initList = self.db[str(Guild)][str(Category)]
        output = list(initList.find({}))
        output.sort(key=init_order, reverse=True)
        for i in output:

            del i["_id"]

        return output

    def turn_next(self, Guild, Category):

        current = self.db[str(Guild)].find_one_and_update(
            {"Category": Category}, {"$inc": {"turn": 1}}, upsert=True
        )
        entries = self.db[str(Guild)][str(Category)].count_documents({})

        if current["turn"] >= entries:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$inc": {"turn": -entries}}
            )

    def turn_get(self, Guild, Category):

        turnCheck = self.db[str(Guild)].find_one({"Category": Category})
        try:
            return turnCheck["turn"]
        except:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$set": {"turn": 1}}, upsert=True,
            )
            turnCheck = self.db[str(Guild)].find_one({"Category": Category})
            return turnCheck["turn"]

    def current_init(self, Guild, Category):

        turnCheck = self.db[str(Guild)].find_one({"Category": Category})["turn"]
        initList = list(self.db[str(Guild)][str(Category)].find({}))
        initList.sort(key=init_order, reverse=True)

        return initList[turnCheck - 1]["ID"]

    def add_owner(self, Guild, Category, ID):
        existCheck = self.db[str(Guild)].find_one({"Category": Category})

        try:
            if existCheck["owner"] == ID:
                output = (
                    "It looks like you're already the owner of this channel category."
                )
                return output
            else:
                currentDM = existCheck["owner"]
                output = f"<@{currentDM}> is currently the DM of this category. In order to take ownership, speak with them or a server administrator."
                return output

        except KeyError:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$set": {"owner": ID}}, upsert=True
            )
            output = f"<@{ID}> has been added as the DM for this channel category."
            return output

        except TypeError:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$set": {"owner": ID}}, upsert=True
            )
            output = f"<@{ID}> has been added as the DM for this channel category."
            return output

    def remove_owner(self, Guild, Category, ID, override=False):
        if override == True:
            current = self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$unset": {"owner": 1}}
            )
            owner = current["owner"]
            output = f"<@{owner}> has been removed as this channel's owner."
            return output
        else:
            current = self.db[str(Guild)].find_one({"Category": Category})
            owner = current["owner"]
            if ID == owner:

                self.db[str(Guild)].find_one_and_update(
                    {"Category": Category}, {"$unset": {"owner": 1}}
                )
                output = f"<@{owner}> has been removed as this channel's owner."
                return output
            else:
                output = f"<@{owner}> is the current owner for this category. Please see an administrator or speak with the current owner to take control."
                return output

    def owner_check(self, Guild, Category, ID):
        if self.db[str(Guild)].find_one({"Category": Category})["owner"] == ID:
            check = True
            return check
        else:
            check = False
            return check

    def add_char(self, Guild, Category, ID, Name):
        
        try:
            char = self.db[str(Guild)].find_one({"Category":Category,"Name":Name})["Name"]
            output = f"{char} is already registered."
            return output
        except:
            entry = {"Name":Name, "Category":Category, "owner": ID, "inv":{}, "spells":{}, "HP":0,"HPmax":0, "SP":0}
            self.db[str(Guild)].insert_one(entry).inserted_id
            output = f"{Name} was added to the database."
            return output

    def remove_char(self, Guild, Category, ID, Name):
        query = {"Name": Name}
        try:
            if ID == self.db[str(Guild)].find_one(query)['owner'] or self.owner_check(Guild, Category, ID) == True:
                self.db[str(Guild)].delete_one(query)
                output = f"{Name} has been removed."
                return output
            else:
                output = f"{Name} doesn't belong to you."
                return output
        except TypeError:
            output = f"{Name} doesn't seem to exist in this category."
            return output
