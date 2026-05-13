
caminho_ficheiro = "new_labeled_data/aruba.txt" # Muda para o dataset que queres usar
sensores_unicos = set()

with open(caminho_ficheiro, "r") as f:
    for linha in f:
        partes = linha.strip().split()
        # O formato CASAS tem a data, a hora e depois o sensor (índice 2)
        if len(partes) >= 3:
            sensor = partes[2]
            # Vamos garantir que apanhamos sensores de Movimento (M), Porta (D), Temp (T), etc.
            if sensor.startswith(('M', 'D', 'T', 'L')): 
                sensores_unicos.add(sensor)

# Ordenar alfabeticamente para ficar bonito
lista_ordenada = sorted(list(sensores_unicos))

print("Copia este dicionário para o teu simulator.py:")
print("{")
for s in lista_ordenada:
    print(f'    "{s}": 0.0,')
print("}")