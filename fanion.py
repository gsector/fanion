import requests
import json
import datetime
from twilio.rest import TwilioRestClient
import config


def weather_by_location():
    ''' Yield the weather for each location '''

    for l in config.locations:
        l['latlong'] = l['lat'] + ',' + l['long']
        # r = requests.get(config.dark_sky['url'] + loc["latlong"]).json()
        r = requests.get(config.dark_sky['url'] + l["latlong"] + ',1476428400').json() # -- Test Day with Rain
                
        assert l['lat'] == str(r['latitude']), 'Result latitude {} too far from {}.'.format(r['latitude'], l['lat'])
        assert l['long'] == str(r['longitude']), 'Result longitude {} too far from {}.'.format(r['longitude'], l['long'])

        r['name'] = l['name']
        yield r


def find_rain():
    ''' Cycles through each location looking for rain '''
    rain_start = None
    rain_end = None
    rain_data = list()

    for r in weather_by_location():
        
        # Don't worry about location if the rain probability is not high
        p_rain = float(r["daily"]["data"][0]["precipProbability"])
        if p_rain < config.min_rain:
            continue
        
        # There is rain, when is it?
        for h in r["hourly"]["data"]:

            # If the threshold isn't hit, skip this hour
            if h['precipProbability'] < config.min_rain:
                continue

            # If rain is outside time range, skip this hour
            rain_hour = int(datetime.datetime.fromtimestamp(h['time']).strftime('%H'))
            if rain_hour < config.time_range['start'] or (rain_hour > config.time_range['end'] and rain_start is None):
                continue
            
            # Get 'pretty' rain time start and end
            rain_time_pretty = datetime.datetime.fromtimestamp(h['time']).strftime('%I%p')
            if rain_start is None:
                rain_start = rain_time_pretty
                rain_end = rain_time_pretty
            else:
                rain_end = rain_time_pretty
        
        # Store Results
        if rain_start:
            rain_data.append({
                'name': r['name'],
                'start': rain_start.lower(),
                'end': rain_end.lower()
            })

    # Return Data
    return rain_data


def create_message(rain_data):
    ''' Create message for rain Data '''
    msg = '☔ Rain Today! ☔'
    # msg += '     .-^-.\n'
    # msg += '    \'"\'|`"`'
    for d in rain_data:
        msg += '\n    {}: {} - {}'.format(d["name"], d['start'], d['end'])
    return msg


def send_message(msg):
    ''' Send text message with data from msg '''
    # If rain, send the message!
    twilio_client = TwilioRestClient(config.twilio['ACCOUNT_SID'], config.twilio['AUTH_TOKEN'])
    for to in config.recipients:
        twilio_message = twilio_client.messages.create(
            to = to, 
            from_ = config.twilio['from'],
            body = msg
        )

def other():
    # Get weather data via API
    for l in weather_by_location():
        r = requests.get(config.dark_sky['url'] + loc["latlong"]).json()
        # r = requests.get(config.dark_sky['url'] + loc["latlong"] + ',1476428400').json() # -- Test Day with Rain

        with open('test.json','w') as f:
            f.write(r.text)

        loc["precip"] = float(r["daily"]["data"][0]["precipProbability"])
        loc["start"] = ''
        if loc["precip"] > 0.15:
            for hour in r["hourly"]["data"]:
                if float(hour['precipProbability']) >= loc["precip"]:
                    loc["start"] = datetime.datetime.fromtimestamp(hour['time']).strftime('%I %p')
                    break

    # Find if there was rain for one of the locations
    for loc in config.locations:
        if loc["precip"] > 0:
            smsTxt = rainMessage(config.locations)
            break # Only need to do this once

    # If rain, send the message!
    try:
        for toPhone in config.phoneList:
            try:
                config.client.messages.create(
                    to=toPhone, 
                    from_=config.fromPhone, 
                    body=smsTxt
                )
            except Exception as e:
                print('Argh!')
                print(e)
    except:
        print('No Rain')



if __name__ == '__main__':
    rain_data = find_rain()

    if rain_data:
        msg = create_message(rain_data)
        sent = send_message(msg)
    
    print('{}'.format(msg))