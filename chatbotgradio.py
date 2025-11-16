from dotenv import load_dotenv
load_dotenv(override=True)

import os
import mlflow
import gradio as gr
from openai import OpenAI
import time
from datetime import datetime
import json


# CONFIG MLflow
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-server:5000"))
mlflow.set_experiment("translation-app-openrouter")


open_router_api_key = os.getenv("OPEN_ROUTER_API_KEY")
open_router_ai = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=open_router_api_key,
    timeout=30.0
)

languages = {
    "Spanish": "Spanish",
    "English": "English",
    "French": "French",
    "German": "German",
    "Italian": "Italian",
    "Portuguese": "Portuguese",
    "Chinese": "Chinese",
    "Japanese": "Japanese"
}

provider_models = {
    "Google": [
        "google/gemma-3-27b-it:free",
        "google/gemini-2.0-flash-exp:free",
    ],
    "Qwen": [
        "qwen/qwen3-14b:free",
        "qwen/qwen-2.5-72b-instruct:free",
    ],
    "DeepSeek": [
        "deepseek/deepseek-r1-distill-llama-70b:free",
        "deepseek/deepseek-r1-0528-qwen3-8b:free"
    ]
}

# FUNCIÓN DE TRADUCCIÓN + MLflow

def traducir_con_mlflow(texto_origen, idioma_origen, idioma_destino, modelo_seleccionado):
    start_time = time.time()

    # Usar nombres descriptivos para los runs
    run_name = (
        f"{idioma_origen}_to_{idioma_destino}_"
        f"{datetime.now().strftime('%H-%M-%S')}_"
        f"{modelo_seleccionado.replace('/', '_')}"
    )

    with mlflow.start_run(run_name=run_name):
        try:
            # -----------------------------
            # PARAMS
            # -----------------------------
            mlflow.log_param("idioma_origen", idioma_origen)
            mlflow.log_param("idioma_destino", idioma_destino)
            mlflow.log_param("modelo", modelo_seleccionado)

            # Extra: proveedor sacado del diccionario
            proveedor_detectado = next((p for p, ms in provider_models.items() if modelo_seleccionado in ms), "Unknown")
            mlflow.log_param("proveedor", proveedor_detectado)

            mlflow.log_param("input_length", len(texto_origen))


            # -----------------------------
            # OPENROUTER REQUEST
            # -----------------------------
            system_prompt = (
                f"Eres un traductor profesional. Traduce del {idioma_origen} "
                f"al {idioma_destino}. Solo devuelve la traducción."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",  "content": texto_origen}
            ]
            
            completion = open_router_ai.chat.completions.create(
                model=modelo_seleccionado,
                messages=messages,
                max_tokens=800,
                temperature=0.3
            )
            
            texto_traducido = completion.choices[0].message.content.strip()

            latencia_ms = (time.time() - start_time) * 1000

            #metrics
            mlflow.log_metric("latencia_ms", latencia_ms)
            mlflow.log_metric("output_length", len(texto_traducido))

            if len(texto_origen) > 0:
                mlflow.log_metric("length_ratio", len(texto_traducido) / len(texto_origen))
            else:
                mlflow.log_metric("length_ratio", 0)

            # ARTIFACT JSON
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "provider": proveedor_detectado,
                "model": modelo_seleccionado,
                "source_language": idioma_origen,
                "target_language": idioma_destino,
                "original_text": texto_origen,
                "translated_text": texto_traducido,
                "latency_ms": latencia_ms
            }

            with open("translation.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            mlflow.log_artifact("translation.json")
            os.remove("translation.json")

            return texto_traducido, f"{latencia_ms:.1f} ms"

        except Exception as e:
            return f"Error en la traducción: {str(e)}", "0.0 ms"


    #update models when provider changes
def actualizar_modelos(proveedor):
    return gr.update(
        choices=provider_models[proveedor],
        value=provider_models[proveedor][0]
    )


# INTERFAZ GRADIO

with gr.Blocks(title="Traductor con MLflow & OpenRouter", theme="soft") as demo:

    gr.Markdown("# Traductor Multilingüe con MLflow")

    #  Texto a traducir y traducción están arriba (como pediste)
    texto_input = gr.Textbox(
        label="Texto a Traducir",
        placeholder="Escribe aquí el texto...",
        lines=3
    )

    traduccion_output = gr.Textbox(
        label="Traducción",
        lines=3,
        interactive=False
    )

    with gr.Row():
        proveedor = gr.Dropdown(
            list(provider_models.keys()),
            label="Proveedor del Modelo",
            value="Google"
        )
        
        modelo = gr.Dropdown(
            provider_models["Google"],
            label="Modelo de IA",
            value=provider_models["Google"][0]
        )

    with gr.Row():
        idioma_origen = gr.Dropdown(
            list(languages.keys()),
            label="Idioma Origen",
            value="Spanish"
        )
        
        idioma_destino = gr.Dropdown(
            list(languages.keys()),
            label="Idioma Destino",
            value="English"
        )
    
    with gr.Row():
        btn_traducir = gr.Button("Traducir", variant="primary", size="lg")
        btn_limpiar = gr.Button("Limpiar")

    tiempo_inferencia = gr.Textbox(
        label="Tiempo de Inferencia",
        value="0.0 ms",
        interactive=False
    )

    proveedor.change(actualizar_modelos, inputs=[proveedor], outputs=[modelo])

    btn_traducir.click(
        traducir_con_mlflow,
        inputs=[texto_input, idioma_origen, idioma_destino, modelo],
        outputs=[traduccion_output, tiempo_inferencia]
    )

    btn_limpiar.click(
        lambda: ("", "", "0.0 ms"),
        outputs=[texto_input, traduccion_output, tiempo_inferencia]
    )

    gr.Markdown("---\n### Monitoreo con MLflow\nPuedes ver tus runs registrados en tu MLflow UI.")



if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
