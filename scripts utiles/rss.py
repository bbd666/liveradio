import feedparser

url = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m" 

feed = feedparser.parse(url)

for entry in feed.entries:
    # Titre
    title = entry.title
    print(title)
    description = entry.description
    print(description)
##    # Date de publication
##    published = entry.published
##    print(published)
##    # Permalink
##    link = entry.link
##    print(link)
##    # Description sommaire
##    summary = entry.summary
##    print(summary)
##    # Le contenu HTML
##    content = entry.content
##    #print(content)
##    print('')
