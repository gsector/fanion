''' Script that gets the weather for one or more configured locations
    and then sends a text message to configured phone numbers
    to notify that there is rain. '''

import datetime, logging
import config
import requests
from twilio.rest import Client

logging.basicConfig(level=logging.DEBUG, 
                    format=' %(asctime)s - %(levelname)s - %(message)s',
                    filename='logging_log.txt')


def weather_by_location():
    ''' Yield the weather for each location '''

    for loc in config.locations:
        logging.info('Checking location {}'.format(loc['name']))

        # Create/get request for weather from the lat/long of the location
        loc['latlong'] = loc['lat'] + ',' + loc['long']
        res = requests.get(config.dark_sky['url'] + loc["latlong"]).json()
        # res = requests.get(config.dark_sky['url'] + loc["latlong"] + ',1476428400').json() # -- Test Day with Rain
        
        # Assert that the location returned matches the location provided.   
        assert loc['lat'] == str(res['latitude']), 'Result latitude {} too far from {}.'.format(res['latitude'], loc['lat'])
        assert loc['long'] == str(res['longitude']), 'Result longitude {} too far from {}.'.format(res['longitude'], loc['long'])

        res['name'] = loc['name']
        yield res


def find_rain():
    ''' Cycles through each location looking for rain '''

    logging.info('Start of find_rain() function.')

    rain_start = None
    rain_end = None
    rain_data = list()

    for r in weather_by_location():
        logging.debug('Searching for rain in {}'.format(r['name']))
        
        # Don't worry about location if the rain probability does not meet threshold
        p_rain = float(r["daily"]["data"][0]["precipProbability"])
        logging.debug('Overall probability is {}, min configured is {}'.format(p_rain, config.min_rain))
        
        if p_rain < config.min_rain:
            continue
        
        # There is rain, when is it?
        logging.info('Checking for rain hour by hour.')
        for h in r["hourly"]["data"]:
            rain_hour = int(datetime.datetime.fromtimestamp(h['time']).strftime('%H'))
            
            # If the threshold isn't hit, skip this hour
            if h['precipProbability'] < config.min_rain:
                logging.debug('T: {}, P: {} -> P too low'.format(rain_hour, h['precipProbability']))
                continue

            # If rain is outside time range, skip this hour
            rain_hour = int(datetime.datetime.fromtimestamp(h['time']).strftime('%H'))
            if rain_hour < config.time_range['start'] or (rain_hour > config.time_range['end'] and rain_start is None):
                logging.debug('T: {}, P: {} -> Time out of range {}, {}'.format(
                    rain_hour, h['precipProbability'], config.time_range['start'], config.time_range['end']
                ))
                continue
            
            # Get 'pretty' rain time start and end
            rain_time_pretty = datetime.datetime.fromtimestamp(h['time']).strftime('%I%p')
            if rain_start is None:
                rain_start = rain_time_pretty
                rain_end = rain_time_pretty
            else:
                rain_end = rain_time_pretty
            logging.debug('Found rain in {}, start: {} and end: {}'.format(r['name'], rain_start, rain_end))
        
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

    logging.info('Creating txt message.')

    msg = '☔ Rain Today! ☔'
    # msg += '     .-^-.\n'
    # msg += '    \'"\'|`"`'
    for d in rain_data:
        msg += '\n    {}: {} - {}'.format(d["name"], d['start'], d['end'])
    
    logging.info('Text message content: \n{}'.format(msg))

    return msg


def send_message(msg):
    ''' Send text message with data from msg '''

    logging.info('Sending txt message(s).')

    # If rain, send the message!
    twilio_client = Client(config.twilio['ACCOUNT_SID'], config.twilio['AUTH_TOKEN'])
    for to in config.recipients:
        twilio_message = twilio_client.messages.create(
            to = to, 
            from_ = config.twilio['from'],
            body = msg
        )

        logging.debug('Sent txt message to {}'.format(to))


if __name__ == '__main__':
    ''' Gets weather data and sends a text message if there is rain '''
    
    logging.info('Start of program.')
    rain_data = find_rain()

    if rain_data:
        logging.info('Rain found, processing txt message.')
        msg = create_message(rain_data)
        send_message(msg)
    if not rain_data:
        logging.info('Rain not found, no message to send.')
    
    logging.info('End of program.')
