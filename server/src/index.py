# This is the code
# Find me on discord ZDev1#4511
# We shouldn't install flask in the terminal, it is already imported
from flask import Flask

from SPConfig import SPConfig

app = Flask(__name__)


# route
@app.route('/')
# route function
def home():
    spconfig = SPConfig()
    return 'hey! The last version is {}'.format(spconfig.get_version_form_spboard())


@app.route('/stack')
def stack():
    spconfig = SPConfig()
    version = spconfig.get_version_form_spboard()
    spconfig.auth_spconfig()
    name = spconfig.create_idp_stack(version)
    return 'Stack Name: {}'.format(name)



# listen
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
    # if you need to make it live debuging add 'debug=True'
    # app.run(port=3000, debug=True)

# Hope you enjoyed ;)
