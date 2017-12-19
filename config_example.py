
# List of locations to check the weather for
locations = [{'name': 'SF',
              'lat': '37.782211',
              'long': '-122.410354'},
             {'name': 'Other Location',
              'lat': '50',
              'long': '160'}]

# Twilio Account Information
twilio = {'ACCOUNT_SID': 'ASDFLASKDJFLKSADNFLKASDNF',
          'AUTH_TOKEN': 'asldfj;alsdkjf2l3kjr2309',
          'from': '+1234567'}

# Base URL for Dark Sky to get weather data
dark_sky = {'url': 'https://api.darksky.net/forecast/e46c48460fc64c04998f216fdf8be52f/'}

# List of recipients to send SMS messages to
recipients = ['+1234567',
              '+1234567']

# Rain threshold, example, 0.15 = minimum 15% chance of rain
min_rain = 0.15

# Time range in "24 hour"
time_range = {'start': 7,
              'end': 19}
