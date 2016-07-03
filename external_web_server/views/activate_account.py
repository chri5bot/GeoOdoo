import crypter
import openerp_client

def response(app,request):
    customer = token = id = ""
    error = False
    cipher = crypter.AESCipher("solutandi1811")
    try:
        try:
            id = request.args["id"]
        except:
            pass

        try:
            token = request.args["token"]
        except:
            pass

        if id:
            customer = cipher.encrypt(id)
        if token:
            customer = cipher.decrypt(token)
            connection = openerp_client.get_connection(hostname="localhost", database="tellevo", login="admin", password="admin")
            customer_model = connection.get_model("gt.customer")
            ids = customer_model.search([("email", "=", customer)])
            if len(ids) == 1:
                customer_model.write(ids, {'state': 'active'})
            else:
                raise Exception('La cuenta no existe!')
    except Exception, e:
        print(e)
        error = True

    return app.render_template('activate_account.html', error=error, customer=customer)
