import os, json, re

### Utility generiche di lettura / scrittura file
def save_dictionary(dict,dest_filename):
    with open(dest_filename,'w') as f:
        json.dump(dict,f,indent=4)

def read_dictionary(source_filename):
    if os.path.isfile(source_filename):
        with open(source_filename, 'r') as f:
            return json.load(f)
    return {}

def save_set(set, dest_filename):
    with open(dest_filename, 'w') as f:
        for item in set:
            f.write(str(item) + '\n')

def read_set(source_filename):
    result = set()
    with open(source_filename,'r') as f:
        for line in f:
            result.add(line.strip())
    return result

def read_dict_from_csv(source_filename):
    result = []
    columns = []
    with open(source_filename, 'r') as f:
        header = f.readline()
        for col in header.split(';'):
            col_data = col.strip()
            if(col_data != ''):
                columns.append(col_data)
        for row in f.readlines():
            cur_row_result = {}
            cur_row_data = row.split(';')
            for i in range(len(columns)):
                cur_row_result[columns[i]] = cur_row_data[i].strip()
            result.append(cur_row_result)

    return result
