import logging, os, openai, tiktoken, threading
COMPLETION_SIZE=int(os.environ['COMPLETION_SIZE'])

def run_prompt(prompt,max_tokens):
    openai.api_key = os.environ['OPENAI_KEY']
    response = openai.Completion.create(model="text-davinci-003", prompt=prompt, temperature=1, max_tokens=max_tokens,  top_p=0.1, frequency_penalty=0,presence_penalty=0)
    return response.choices[0].text

def stop_thread(t):
    logging.warn(f"Stopping thread run_prompt..")
    t._stop()


def run_prompt_thread(prompt,max_tokens):
    t = threading.Thread(target=run_prompt, args=(prompt,max_tokens,))
    timer = threading.Timer(10, stop_thread, args=(t,))
    t.start()
    timer.start()
    logging.info("Launched thread run_prompt..")
    result = t.get()
    return result

def get_new_resume(messages):
    prompt_context=f"Puoi farmi un riassunto dei seguenti messaggi di chat, senza inventare fatti? I messaggi sono rappresentati come\nutente: messaggio\n"
    for message in messages:
        prompt_context = prompt_context + f"{message['username']}: {message['text']}\n"
    prompt_context=prompt_context+"Riassunto:\n"
    result = run_prompt(prompt_context,COMPLETION_SIZE)
    return result


def get_incremental_resume(cur_resume,messages):
    prompt_context=f"Dato il seguente riassunto: \nRiassunto: {cur_resume}\nPuoi farmi un nuovo riassunto, senza inventare fatti, che include anche i seguenti messaggi di chat? I messaggi sono rappresentati come\nutente: messaggio\n"
    for message in messages:
        prompt_context = prompt_context + f"{message['username']}: {message['text']}\n"
    prompt_context=prompt_context+"Riassunto:\n"
    result = run_prompt(prompt_context,COMPLETION_SIZE)
    return result

def estimate_tokens(prompt):
    enc = tiktoken.get_encoding("gpt2")
    encoded = enc.encode(prompt)
    return len(encoded)