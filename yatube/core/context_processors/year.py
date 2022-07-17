from datetime import datetime


def year(request):
    return {
        'year': int(datetime.now().strftime('%Y')),
    }
