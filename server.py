import os
import RSA_Methods
import pickle
import socket
import threading
from Crypto.Hash import SHA256
import mysql.connector
from mysql.connector import Error


def hash_package(package):
    hasher = SHA256.new()
    hasher.update(pickle.dumps(package))

    packageWithHash = {
                "package" : package,
                "hash" : hasher.hexdigest()
    }

    return packageWithHash

def hash_matches(package, hash):
    hasher = SHA256.new()
    hasher.update(pickle.dumps(package))

    return hash == hasher.hexdigest()

def hash_value_with_salt(value, salt = os.urandom(32)):
    value = value.encode() + salt
    hasher = SHA256.new()
    hasher.update(value)

    return hasher.hexdigest(), salt.hex()

def listen_for_connections():
    socketObj.listen()

    while(1):
        clientSocket, clientAddress = socketObj.accept()
        print("Server> Connected to address: ", clientAddress)
        # send the server public key to client here

        request_handler = threading.Thread(target=listen_for_requests, args=(clientSocket, clientAddress))
        request_handler.start()

def listen_for_requests(clientSocket, clientAddress):
    request = clientSocket.recv(2048)

    # decrypt package with server private key first here

    packageWithHash = pickle.loads(request)
    package = packageWithHash["package"]
    
    if not hash_matches(package, packageWithHash["hash"]):
        print("Server> Received request was corrupted.")
        return

    header = package["header"]

    if header == "register":
        handle_register_request(clientSocket, package)
    elif header == "login":
        handle_login_request(clientSocket, package)
    elif header == "listgroup":
        handle_listgroup_request(clientSocket, package)
    elif header == "creategroup":
        handle_creategroup_request(clientSocket, package)
    elif header == "entergroup":
        handle_entergroup_request(clientSocket, package)
    elif header == "sendmessage":
        handle_sendmessage_request(clientSocket, package)
    elif header == "addusertogroup":
        handle_addusertogroup_request(clientSocket, package)
    elif header == "leavegroup":
        handle_leavegroup_request(clientSocket, package)

# main functionality
def handle_register_request(clientSocket, package):
    try:
        dbcursor = dbconnection.cursor()
        dbcursor.execute("SELECT username FROM Users WHERE username = %s;", (package["username"],))
        rows = dbcursor.fetchall()

        if len(rows) > 0:
            responsePackage = "exists"
        else:
            hashedPassword, salt = hash_value_with_salt(package["password"])
            dbcursor.execute("INSERT INTO Users VALUES(%s, %s, %s, %s);", (package["username"], hashedPassword, salt, pickle.dumps(package["key"]),))
            dbconnection.commit()

            print("Server> User registered.")
            responsePackage = "success"
        
        try:
            packageWithHash = hash_package(responsePackage)
            serializedData = pickle.dumps(packageWithHash)
            encryptedData = RSA_Methods.encrypt(RSA_Methods.RSA.import_key(package["key"]), serializedData)
            clientSocket.send(encryptedData)
        except:
            print("Server> Could not send response.")
            dbcursor.execute("DELETE FROM Users WHERE username = %s;", (package["username"],))
            dbconnection.commit()
            print("Server> User registration cancelled.")
    except:
        print("Server> Server ran into an unspecified error.")
    finally:
        clientSocket.close()

def handle_login_request(clientSocket, package):
    try:
        dbcursor = dbconnection.cursor()
        dbcursor.execute("SELECT * FROM Users WHERE username = %s;", (package["username"],))
        rows = dbcursor.fetchall()

        if len(rows) == 0:
            responsePackage = "no user"
        else:
            checkPassword, temp = hash_value_with_salt(package["password"], bytes.fromhex(rows[0][2]))
            if rows[0][1] == checkPassword:
                responsePackage = "logged"
                print("Server> User logged in.")
            else:
                responsePackage = "wrong pass"

        try:
            packageWithHash = hash_package(responsePackage)
            serializedData = pickle.dumps(packageWithHash)
            clientSocket.send(serializedData)
        except:
            print("Server> Could not login send response.")

    except Exception as e:
        print("Server> Could not login user due to unspecified error.\n", e)
    finally:
        clientSocket.close()

def handle_listgroup_request(clientSocket, package):
    pass

def handle_creategroup_request(clientSocket, package):
    pass

def handle_entergroup_request(clientSocket, package):
    pass

def handle_sendmessage_request(clientSocket, package):
    pass

# additional functionality
def handle_addusertogroup_request(clientSocket, package):
    pass

def handle_leavegroup_request(clientSocket, package):
    pass

try:
    dbconnection = mysql.connector.connect(host='localhost', database='IS_Chat', user='root', password='Astera@123456')
    if dbconnection.is_connected():
        print("Server> Connected to mysql server. ")
except Error as e:
    print("Server> Error while connecting to database server.", e)

server_ip = "localhost"
server_port = 7000
# generate server keys here

try:
    socketObj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketObj.bind((server_ip, server_port))
except Exception as e:
    print("Server> Could not initialize server.")
    exit(-1)

listen_for_connections()