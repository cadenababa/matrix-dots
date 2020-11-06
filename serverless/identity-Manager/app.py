from chalice import Chalice
import boto3
from chalicelib import Address, jsonify, dynamoDb, Authenticator
from chalicelib.config import Config
from chalicelib.blueprint import BluePrintRegister
from chalicelib.decorators import jwt_required

app = Chalice(app_name='identity-Manager')
app.register_blueprint(BluePrintRegister.bluePrintIns)
dynamodb = boto3.resource('dynamodb')

@app.route('/v1/get-token')
def get_token():
    username = app.current_request.query_params.get('username')
    dydbTableObj = dynamodb.Table(Config.service_user_holder_table)
    resp = dydbTableObj.get_item(Key={'username': username}) 
    try:
        Item = resp.get('Item')
        if not Item.get('is_active'): return jsonify(message='Inactive username', is_token=False)
    except: return jsonify(message='Invalid username', is_token=False)
    jwtToken = (Authenticator.create_token(username)).decode('utf-8')
    return jsonify(jwt_token=jwtToken, is_token=True)

@app.route('/v1/get-address')
@jwt_required
def get_address():
    mnemonic, address, colab, uuid = Address.generate_the_base()
    data = {'mnemonic': mnemonic, 'address': address, 'colab':colab, 'uuid': uuid}
    dynamoDb.put_data(data=data)
    return jsonify(mnemonic=mnemonic, address=address, colab=colab, uuid=uuid)

@app.route('/v1/recover-account') # forgot uuid (only possiable recovery item)
@jwt_required
def recover_account():
    mnemonic = app.current_request.query_params.get('mnemonic')
    if not mnemonic: return jsonify(message='enter a valid mnemonic', is_recovered=False)
    table = dynamodb.Table(Config.identity_dydb_table)
    allItems = dynamoDb.get_all_data(table)
    for item in allItems:
        if item.get('mnemonic') == mnemonic: return jsonify(message='account found', uuid=item.get('uuid'))
    return jsonify(message='Invalid mnemonic')