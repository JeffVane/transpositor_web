from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import os
import librosa
import soundfile as sf
import numpy as np
from werkzeug.utils import secure_filename
import time
import json
import requests
import webbrowser

def verificar_versao():
    try:
        # Lê a versão local do arquivo
        with open("version.txt", "r") as f:
            versao_local = f.read().strip()

        # Lê a versão publicada online (altere a URL para seu repositório real)
        url = "https://raw.githubusercontent.com/JeffVane/transpositor_web/main/version.txt"
        resposta = requests.get(url)
        versao_remota = resposta.text.strip()

        # Compara as versões
        if versao_remota > versao_local:
            print(f"\n🔔 Nova versão disponível: {versao_remota}")
            print("Abrindo página de atualização...")
            webbrowser.open("https://github.com/SEU_USUARIO/transpositor_web/releases/latest")
        else:
            print("✅ Você está usando a versão mais recente.")
    except Exception as e:
        print(f"⚠️ Erro ao verificar atualizações: {e}")


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'static/processed'
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB limite máximo

# Garantir que as pastas existam
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(os.path.join(STATIC_FOLDER, 'css'), exist_ok=True)
os.makedirs(os.path.join(STATIC_FOLDER, 'js'), exist_ok=True)

# Notas musicais em ordem
NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def transpor_tom(original, semitones):
    """
    Retorna o nome do tom resultante da transposição de 'original' por 'semitones'.
    """
    try:
        idx = NOTAS.index(original)
        novo_idx = (idx + semitones) % 12
        return NOTAS[novo_idx]
    except ValueError:
        return f"{semitones:+d}"  # fallback se o tom original for inválido


# Mapeamento de índices de tons para nomes
KEY_NAMES = [
    'C', 'C#', 'D', 'D#', 'E', 'F',
    'F#', 'G', 'G#', 'A', 'A#', 'B'
]

# Nomes alternativos com bemóis
KEY_NAMES_FLAT = [
    'C', 'Db', 'D', 'Eb', 'E', 'F',
    'Gb', 'G', 'Ab', 'A', 'Bb', 'B'
]


def detect_key(audio_path):
    """Detecta o tom da música usando algoritmos do librosa"""
    try:
        # Carregar áudio
        y, sr = librosa.load(audio_path, sr=None)

        # Extrair features cromáticas
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

        # Calcular o perfil de tom (key profile)
        chroma_avg = np.mean(chroma, axis=1)

        # Obter o índice do tom mais provável
        key_idx = np.argmax(chroma_avg)

        # Análise para determinar modo maior/menor
        # Comparação simples baseada no intervalo de terça
        major_third = (key_idx + 4) % 12
        minor_third = (key_idx + 3) % 12

        if chroma_avg[major_third] > chroma_avg[minor_third]:
            mode = "maior"  # major
            key_name = KEY_NAMES[key_idx]
        else:
            mode = "menor"  # minor
            key_name = KEY_NAMES[key_idx]

        return {
            "key_idx": int(key_idx),
            "key_name": key_name,
            "mode": mode,
            "full_key": f"{key_name} {mode}"
        }
    except Exception as e:
        print(f"Erro ao detectar tom: {str(e)}")
        return {
            "key_idx": -1,
            "key_name": "Desconhecido",
            "mode": "desconhecido",
            "full_key": "Tom não detectado"
        }


def get_new_key(original_key_idx, semitones, mode):
    """Calcula o novo tom após a transposição"""
    if original_key_idx == -1:
        return "Desconhecido"

    new_idx = (original_key_idx + semitones) % 12

    # Escolhe entre usar # ou b baseado no ciclo de quintas
    # Tons com sustenidos: G, D, A, E, B, F#, C#
    # Tons com bemóis: F, Bb, Eb, Ab, Db, Gb, Cb
    sharps_keys = [7, 2, 9, 4, 11, 6, 1]  # G, D, A, E, B, F#, C#

    if new_idx in sharps_keys:
        key_name = KEY_NAMES[new_idx]
    else:
        key_name = KEY_NAMES_FLAT[new_idx]

    return f"{key_name} {mode}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    # Debug info
    print("Request recebida em /upload-audio")
    print(f"Files: {request.files}")

    # Verificar se há um arquivo na requisição
    if 'file' not in request.files:
        print("Erro: 'file' não encontrado nos arquivos da requisição")
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    print(f"Nome do arquivo: {file.filename}")

    # Verificar se o nome do arquivo está vazio
    if file.filename == '':
        print("Erro: Nome de arquivo vazio")
        return jsonify({"error": "Nome de arquivo inválido"}), 400

    # Verificar se é um arquivo .wav ou aceitar todos os formatos de áudio
    accepted_formats = ['.wav', '.mp3', '.ogg', '.flac']
    file_ext = os.path.splitext(file.filename.lower())[1]

    if file_ext not in accepted_formats:
        print(f"Erro: Formato de arquivo não suportado: {file_ext}")
        return jsonify({"error": f"Formato não suportado. Use: {', '.join(accepted_formats)}"}), 400

    try:
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        static_path = os.path.join(PROCESSED_FOLDER, f"original_{safe_filename}")

        # Salva o arquivo enviado
        file.save(file_path)
        print(f"Arquivo salvo em: {file_path}")

        # Converte para WAV se necessário e salva uma cópia na pasta estática
        try:
            y, sr = librosa.load(file_path, sr=None)
            sf.write(static_path, y, sr)
            print(f"Áudio processado e salvo em: {static_path}")
        except Exception as audio_err:
            print(f"Erro ao processar áudio: {str(audio_err)}")
            # Se falhar, tenta simplesmente copiar o arquivo
            import shutil
            shutil.copy(file_path, static_path)
            print("Usando cópia direta do arquivo")

        # Detectar o tom da música
        key_info = detect_key(file_path)
        print(f"Tom detectado: {key_info['full_key']}")

        # Estrutura de dados sobre os tons disponíveis para transposição
        # Limitando a +/- 6 semitons para manter qualidade de áudio
        # Exemplo de construção de available_keys com nomes reais
        # ✅ Adicionado: define o tom original
        original_key = key_info.get("key_name", "C")

        available_keys = []
        for semitones in range(-6, 7):
            if semitones == 0:
                continue

            novo_tom = transpor_tom(original_key, semitones)
            available_keys.append({
                "semitones": semitones,
                "key_name": novo_tom,
                "direction": "acima" if semitones > 0 else "abaixo"
            })

        # Salvar metadados do arquivo para consultas futuras
        metadata = {
            "original_key": key_info,
            "available_keys": available_keys,
            "timestamp": timestamp,
            "filename": safe_filename
        }

        metadata_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{safe_filename}.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        return jsonify({
            "url": f"/static/processed/original_{safe_filename}",
            "filename": safe_filename,
            "original_key": key_info,
            "available_keys": available_keys
        })
    except Exception as e:
        print(f"Erro geral: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/transpose', methods=['POST'])
def transpose_audio():
    try:
        data = request.json

        if not data or 'filename' not in data or 'semitones' not in data:
            return jsonify({"error": "Dados incompletos"}), 400

        filename = data['filename']
        semitones = int(data['semitones'])
        semitones = max(-12, min(12, semitones))

        original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_name = f"transposed_{semitones}_{filename}"
        output_path = os.path.join(PROCESSED_FOLDER, output_name)

        # ⚙️ Se ainda não existe, gera o arquivo
        if not os.path.exists(output_path):
            y, sr = librosa.load(original_path, sr=None)
            y_shifted = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=semitones)
            sf.write(output_path, y_shifted, sr)

        # 📁 Caminho do .json de metadados
        metadata_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}.json")

        # 🔧 Cria ou atualiza metadados
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {
                "filename": filename,
                "original_key": {"full_key": "Desconhecido"},
                "available_keys": [],
                "timestamp": datetime.datetime.now().isoformat()
            }

        # 🔎 Define o nome e direção do novo tom
        # 🧠 Detectar tom transposto corretamente
        original_key = metadata.get('original_key', {}).get('full_key', "Desconhecido")
        if original_key in NOTAS:
            key_name = transpor_tom(original_key, semitones)
        else:
            key_name = f"{'+' if semitones > 0 else ''}{semitones}"

        direction = "acima" if semitones > 0 else "abaixo"
        new_key = {
            "semitones": semitones,
            "key_name": key_name,
            "direction": direction,
            "processed": True
        }

        # ✅ Atualiza ou adiciona o tom ao JSON
        found = False
        for key in metadata["available_keys"]:
            if key["semitones"] == semitones:
                key.update(new_key)
                found = True
                break
        if not found:
            metadata["available_keys"].append(new_key)


        # 💾 Salva de volta o JSON
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        return jsonify({
            "url": f"/static/processed/{output_name}",
            "original_key": metadata.get('original_key', {}).get('full_key', "Desconhecido"),
            "new_key": key_name,
            "semitones": semitones,
            "download_url": f"/download/{output_name}"
        })

    except Exception as e:
        print(f"Erro na transposição: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Endpoint para download do arquivo de áudio transposto"""
    return send_file(
        os.path.join(PROCESSED_FOLDER, filename),
        as_attachment=True,
        download_name=f"transposto_{filename}"
    )


@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/css'), filename)


@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/js'), filename)

@app.route('/processed-audios')
def list_processed_audios():
    files = os.listdir(PROCESSED_FOLDER)
    processed = [f for f in files if f.endswith('.mp3') and f.startswith('transposed_')]

    audios = []
    for filename in processed:
        parts = filename.split('_')
        if len(parts) >= 3:
            semitones = parts[1]
            original_name = "_".join(parts[2:])
            audios.append({
                "semitones": semitones,
                "filename": filename,
                "original_name": original_name,
                "url": f"/static/processed/{filename}"
            })

    return jsonify(audios)


@app.route('/historico')
def historico():
    arquivos = []
    for f in os.listdir(UPLOAD_FOLDER):
        if f.endswith('.json'):
            try:
                caminho_json = os.path.join(UPLOAD_FOLDER, f)
                with open(caminho_json, 'r') as json_file:
                    metadata = json.load(json_file)

                filename = metadata.get("filename")
                timestamp = metadata.get("timestamp")
                original_key = metadata.get("original_key")

                # Recupera os tons salvos
                available_keys = metadata.get("available_keys", [])

                # Atualiza flag `processed` verificando se o arquivo foi gerado
                for key in available_keys:
                    semitones = key.get("semitones")
                    nome_transposto = f"transposed_{semitones}_{filename}"
                    caminho_transposto = os.path.join(PROCESSED_FOLDER, nome_transposto)
                    key["processed"] = os.path.exists(caminho_transposto)

                # Atualiza o próprio arquivo JSON com os `processed` corrigidos
                with open(caminho_json, 'w') as json_out:
                    json.dump({
                        "filename": filename,
                        "original_key": original_key,
                        "available_keys": available_keys,
                        "timestamp": timestamp
                    }, json_out)

                # Adiciona no retorno
                arquivos.append({
                    "filename": filename,
                    "original_key": original_key.get("full_key"),
                    "available_keys": available_keys,
                    "timestamp": timestamp
                })

            except Exception as e:
                print(f"Erro no arquivo {f}: {e}")
                continue

    # Ordena por mais recente
    arquivos.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(arquivos)






if __name__ == '__main__':
    verificar_versao()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
