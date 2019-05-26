import faust


app = faust.App('autoparse', broker='kafka://localhost:9092', value_serializer='raw')

raw_logs_topic = app.topic('raw_logs', value_type=str)
parsed_logs_topic = app.topic('parsed_logs', value_type=str)
log_keys_topic = app.topic('log_keys', value_type=str)

greetings_topic = app.topic('greetings')


@app.agent(greetings_topic)
async def greet(greetings):
    async for greeting in greetings:
        print(greeting)
