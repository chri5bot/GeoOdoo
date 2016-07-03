import crypter
import openerp_client
import datetime
import json

def response(app,request):
    error = False
    arg = ""
    message=""
    m=""
    try:
        try:
            arg = request.args["arg"]
        except:
            pass
        try:
            m = request.args["m"]
        except:
            pass
        connection = openerp_client.get_connection(hostname="localhost", database="tellevo", login="admin", password="admin")
        # customer_model = connection.get_model("gt.customer")
        # message=customer_model.sign_up(False, "TEST_NOMBRE", "TEST_APELLIDO", "1717677478", "cedula", "6", "0900000000", "020000000",
        #         "CARCELEN", "christian.cascante@tandicorp.net", "1111", "1111", "1111")
        # if "customer_id" in message.keys():
        #     user_info = customer_model.search_read([('id', '=', message["customer_id"])], ["partner_id"])[0]
        #     customer_model.unlink(message["customer_id"])
        #     partner_model = connection.get_model("res.partner")
        #     partner_model.unlink([user_info["partner_id"][0]])
        if "confirm" == m:
            model = connection.get_model("gt.route")
            message = model.act_search([int(arg)])
            message = str(message)
        if "find" == m:
            model = connection.get_model("gt.route")
            message = model.find_partners_inrange([2], 3000)
            message = str(message)
        if "chat" == m:
            model = connection.get_model("gt.route")
            message=model.mobile_getchat(2)
            message=str(message)
        if "pschat" == m:
            model = connection.get_model("gt.route")
            message = model.mobile_sendchat(2,1,'PS',str(arg))
            message = str(message)
        if "uschat" == m:
            model = connection.get_model("gt.route")
            message = model.mobile_sendchat(2, 1, 'US', str(arg))
            message = str(message)
        if "activeroute" == m:
            model = connection.get_model("gt.route")
            message = model.mobile_active_routes(1)
        if "route" == m:
            model = connection.get_model("gt.route")
            message = model.mobile_route(int(arg))
            message = str(message)
        if "geopoint" == m:
            model = connection.get_model("gt.travel")
            message = model.get_geopoint_to_google(135, 'geo_point_start')
        if "reasons" == m:
            model = connection.get_model("gt.mobilesetting.ps")
            message = model.mobile_get_reasons_rejection()
            message = str(message)
        if "psinrange" == m:
            model = connection.get_model("gt.route")
            message = model.find_partners_inrange(int(arg))
            message = str(message)
        if "confirmroute" == m:
            model = connection.get_model("gt.route")
            message = model.mobile_confirmroute(int(arg), 'cash')
            message = str(message)
        if "aceptroute" == m:
            model = connection.get_model("gt.service.partner")
            message = model.mobile_acept_route(1, int(arg))
            message = str(message)
        if "updatepsres" == m:
            model = connection.get_model("gt.route")
            message = model.update_partners_response()
            message = str(message)

        if "recharge" == m:
            model = connection.get_model("gt.service.partner")
            message = model.ws_recharge(arg, False, '2016-05-17', 'LA TIENDITA', '1124SC')
            message = str(message)

        if "asksupport" == m:
            model = connection.get_model("gt.service.partner")
            message = model.mobile_ask_support(1, 155, '-78.0', '-0.18', 'TANDICORP')
            message = str(message)

    except Exception, e:
        print(e)
        message = e
        error = True
    return app.render_template('tests.html', error=error, message=message)
