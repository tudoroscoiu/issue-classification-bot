import json
import uvicorn
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from model import factory, loader

app = FastAPI()

class ModelRequest(BaseModel):
    text: Optional[str] = None

class ModelResponse(BaseModel):
    label: Optional[str] = None

with open("config.json") as f:
    data = json.load(f)
    loader.load_plugin(data["plugin"])

    models = {model_data["name"]: factory.create_model(model_data) for model_data in data["models"]}

print("Loaded models:")
for model_name, model_object in models.items():
    print(f"  - {model_name}: {model_object}")

@app.post("/models/{model_name}", response_model=ModelResponse)
def get_model(model_name: str, data: ModelRequest = Body(...)):
    if model_name not in models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    text = data.text

    if text is None:
        raise HTTPException(status_code=400, detail="Input text not found")
    
    model = models[model_name]
    label = None

    if text is not None:
        label = model.label(text)

    return ModelResponse(label=label)

@app.post("/models", response_model=Dict[str, ModelResponse])
def get_models(data: ModelRequest = Body(...)):
    text = data.text

    if text is None:
        raise HTTPException(status_code=400, detail="Text not found")

    results = {}
    
    for model_name, model in models.items():
        label = None

        if text is not None:
            label = model.label(text)

        results[model_name] = ModelResponse(label=label)

    return results


@app.get("/models/names")
def get_model_names():
    return list(models.keys())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")



