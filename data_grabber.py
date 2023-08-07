import requests
import datetime
# import matplotlib.pyplot as plt
import pytz
from typing import Optional


## TODO -- figure out timezone stuff (everything is in EST now)


def call_api(market_url:str, end_id:Optional[str]=None):

    slug = market_url.split("/")[-1]

    if end_id is None:
        api_url = f"https://manifold.markets/api/v0/bets?contractSlug={slug}"

    else:
        api_url = f"https://manifold.markets/api/v0/bets?contractSlug={slug}&before={end_id}"

    response = requests.get(api_url)

    if response.status_code != 200 or len(response.json())==0:

        ## unsuccessfull API call
        return([[] , [], [], ])




    data = response.json()



    prices = []
    times = []
    ids = []
    for i in range(len(data)):
        try:

            ## time since epoch milliseconds
            timestamp_ms = data[i]["createdTime"]


            timestamp_sec = timestamp_ms / 1000
            dt_object = datetime.datetime.utcfromtimestamp(timestamp_sec)

            est = pytz.timezone('US/Eastern')
            time = dt_object.replace(tzinfo=pytz.utc).astimezone(est)



            # time = dt_object.strftime('%Y-%m-%d %H:%M:%S')
            times.append(time)

            prices.append(data[i]["probAfter"])

            ids.append(data[i]["id"])


        except:
            pass


    assert len(times)==len(prices)==len(ids)


    ## TODO -- is reordering necessary?

    combined = list(zip(times, prices,ids))

    sorted_combined = sorted(combined, key=lambda x: x[0])
    times, prices, ids = zip(*sorted_combined)

    times = list(times)
    prices = list(prices)
    ids = list(ids)


    return([times,prices,ids])




def get_data(market_url:str, start_time:Optional[datetime.datetime]=None, end_time:Optional[datetime.datetime]=None, csv_file:Optional[str]=None, interval:Optional[str]=None ):

    print("getting data...")

    times_all = []
    prices_all = []
    ids_all = []


    keep_going = True
    end_id = None

    # request_num = 1

    while keep_going:


        # print(f"Request {request_num}...")

        [times_out, prices_out, ids_out] = call_api(market_url,end_id=end_id)

        # request_num += 1

        # if len(times_out)>0:
        #     print("Successfull.")
        #     print()

        # else:
        #     print("Unsuccessful")
        #     print()


        if start_time is not None:
            if times_out[0] <= start_time:
                keep_going = False

            else:
                end_id = ids_out[0]

        else:
            if len(times_out)==0:
                keep_going = False
            else:
                end_id = ids_out[0]


        times_all = times_out + times_all
        prices_all = prices_out + prices_all
        ids_all = ids_out + ids_all



    combined = list(zip(times_all, prices_all,ids_all))
    sorted_combined = sorted(combined, key=lambda x: x[0])
    times_all, prices_all, ids_all = zip(*sorted_combined)

    times_all = list(times_all)
    prices_all = list(prices_all)
    ids_all = list(ids_all)


    do_time_normalization = 0

    if interval is not None:

        if interval.lower() in ["hour", "hourly","hours"]:
            time_increment = datetime.timedelta(hours=1)
            do_time_normalization = 1

        elif interval.lower() in ["day", "daily", "days"]:
            time_increment = datetime.timedelta(days=1)
            do_time_normalization = 1

        elif interval.lower() in ["minute", "minutes"]:
            time_increment = datetime.timedelta(minutes=1)
            do_time_normalization = 1

        elif interval.lower() in ["second", "seconds"]:
            time_increment = datetime.timedelta(seconds=1)
            do_time_normalization = 1

        else:
            print()
            print("interval not recognized, returning dense output (all timepoints)")
            print()


    if do_time_normalization:


        if start_time is None:
            start_time = times_all[0]

        if end_time is None:
            end_time = times_all[-1]



        current_time = start_time
        time_uniform = []

        while current_time <= end_time:
            time_uniform.append(current_time)
            current_time += time_increment

        if time_uniform[-1] > end_time:
            time_uniform = time_uniform[:-1]



        prices_uniform = []
        ids_uniform = []
        current_ind = 0
        for i in range(len(times_all)-1):
            time = time_uniform[current_ind]

            if times_all[i] <= time and times_all[i+1] > time:
                prices_uniform.append(prices_all[i])
                ids_uniform.append(ids_all[i])

                current_ind += 1

                if current_ind > len(time_uniform)-1:
                    break


        times_all = time_uniform
        prices_all = prices_uniform
        ids_all = ids_uniform



    else:
        if start_time is not None or end_time is not None:
            if start_time is None:
                start_time = times_all[0]

            if end_time is None:
                end_time = times_all[-1]

            times_to_keep = []
            prices_to_keep = []

            for i in range(len(times_all)):
                if times_all[i] >= start_time and times_all[i] <= end_time:
                    times_to_keep.append(times_all[i])
                    prices_to_keep.append(prices_all[i])

            times_all = times_to_keep
            prices_all = prices_to_keep



    if csv_file is not None:

        print("writing csv...")

        with open(csv_file, "w") as record_file:
            record_file.write("time,price\n")

            for i in range(len(times_all)):
                record_file.write(f"{times_all[i]},{prices_all[i]}\n")



    print("done")
    return([times_all, prices_all])

    # return([times_all, prices_all, ids_all])