import json
 
with open('municipios.json', 'r', encoding='utf-8') as f:
    municipios = json.load(f)
 
with open('estados.json', 'r', encoding='utf-8') as f:
    estados_list = json.load(f)
 
estados = {e['c']: e['n'] for e in estados_list}
 
lines = ['DELETE FROM reclutamiento__kuale_city;']
for estado_clave, mlist in municipios.items():
    estado_nombre = estados.get(estado_clave, estado_clave).replace("'", "''")
    for m in mlist:
        city = m['n'].replace("'", "''")
        lines.append(
            "INSERT INTO reclutamiento__kuale_city "
            "(city, state, code, active, settlement, settlement_type, municipality) "
            "VALUES ('{}', '{}', '{}', true, '', '', '{}');".format(
                city, estado_nombre, estado_clave, city
            )
        )
 
with open('cities_win1252.sql', 'w', encoding='cp1252', errors='replace') as f:
    f.write('\n'.join(lines))
 
print('cities_win1252.sql generado con {} registros'.format(len(lines) - 1))