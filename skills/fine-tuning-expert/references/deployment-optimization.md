# Deployment and Optimization for Fine-Tuned Models

> Reference for: Fine-Tuning Expert
> Load when: Model merging, quantization, serving, inference optimization, production deployment

---

## Overview

Deploying fine-tuned models efficiently requires adapter merging, quantization, and inference optimization. This reference covers techniques to minimize latency and memory while maintaining quality.

## Adapter Merging

### Merging LoRA Adapters

```python
from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def merge_lora_adapter(
    base_model_name: str,
    adapter_path: str,
    output_path: str,
    push_to_hub: bool = False,
    hub_repo: str = None
):
    """
    Merge LoRA adapter into base model and save.

    This creates a standalone model without adapter overhead.
    """
    # Load base model
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )

    # Load adapter
    model = PeftModel.from_pretrained(base_model, adapter_path)

    # Merge adapter weights into base model
    print("Merging adapter weights...")
    merged_model = model.merge_and_unload()

    # Save merged model
    print(f"Saving merged model to {output_path}")
    merged_model.save_pretrained(output_path)

    # Save tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    tokenizer.save_pretrained(output_path)

    if push_to_hub and hub_repo:
        print(f"Pushing to hub: {hub_repo}")
        merged_model.push_to_hub(hub_repo)
        tokenizer.push_to_hub(hub_repo)

    return merged_model

# Usage
# merge_lora_adapter(
#     "meta-llama/Llama-3.1-8B",
#     "./lora-adapter",
#     "./merged-model"
# )
```

### Merging Multiple Adapters

```python
from peft import PeftModel

def merge_multiple_adapters(
    base_model_name: str,
    adapters: dict[str, float],
    output_path: str
):
    """
    Merge multiple LoRA adapters with weighted combination.

    Args:
        base_model_name: Base model name or path
        adapters: Dict of {adapter_path: weight}
        output_path: Output path for merged model
    """
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )

    # Load first adapter
    adapter_paths = list(adapters.keys())
    model = PeftModel.from_pretrained(
        base_model,
        adapter_paths[0],
        adapter_name="adapter_0"
    )

    # Load remaining adapters
    for i, adapter_path in enumerate(adapter_paths[1:], 1):
        model.load_adapter(adapter_path, adapter_name=f"adapter_{i}")

    # Combine adapters with weights
    adapter_names = [f"adapter_{i}" for i in range(len(adapters))]
    weights = list(adapters.values())

    model.add_weighted_adapter(
        adapters=adapter_names,
        weights=weights,
        adapter_name="merged",
        combination_type="linear"
    )

    model.set_adapter("merged")
    merged_model = model.merge_and_unload()
    merged_model.save_pretrained(output_path)

    return merged_model

# Usage: Combine coding and chat adapters
# merge_multiple_adapters(
#     "meta-llama/Llama-3.1-8B",
#     {"./coding-lora": 0.6, "./chat-lora": 0.4},
#     "./merged-model"
# )
```

## Quantization

### GPTQ Quantization

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, GPTQConfig
from datasets import load_dataset

def quantize_gptq(
    model_path: str,
    output_path: str,
    bits: int = 4,
    group_size: int = 128,
    calibration_samples: int = 128
):
    """
    Quantize model using GPTQ (post-training quantization).

    GPTQ provides excellent quality with 4-bit quantization.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    # Calibration dataset
    calibration_data = load_dataset("wikitext", "wikitext-2-raw-v1", split="train")
    calibration_texts = calibration_data["text"][:calibration_samples]

    # Tokenize calibration data
    def tokenize(examples):
        return tokenizer(examples, truncation=True, max_length=2048)

    calibration_dataset = [tokenize(text) for text in calibration_texts if text.strip()]

    # GPTQ config
    gptq_config = GPTQConfig(
        bits=bits,
        group_size=group_size,
        dataset=calibration_dataset,
        desc_act=True,  # Activation order for better accuracy
        damp_percent=0.01,
        sym=True  # Symmetric quantization
    )

    # Load and quantize
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="auto",
        quantization_config=gptq_config
    )

    # Save quantized model
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    print(f"Quantized model saved to {output_path}")
    return model

# Usage
# quantize_gptq("./merged-model", "./quantized-gptq-4bit")
```

### AWQ Quantization

```python
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

def quantize_awq(
    model_path: str,
    output_path: str,
    bits: int = 4,
    group_size: int = 128,
    zero_point: bool = True
):
    """
    Quantize model using AWQ (Activation-aware Weight Quantization).

    AWQ is faster than GPTQ and often provides better quality.
    """
    # Load model with AWQ
    model = AutoAWQForCausalLM.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    # Quantization config
    quant_config = {
        "zero_point": zero_point,
        "q_group_size": group_size,
        "w_bit": bits,
        "version": "GEMM"  # GEMM for GPU, GEMV for CPU
    }

    # Quantize
    model.quantize(tokenizer, quant_config=quant_config)

    # Save
    model.save_quantized(output_path)
    tokenizer.save_pretrained(output_path)

    return model

# Usage
# quantize_awq("./merged-model", "./quantized-awq-4bit")
```

### GGUF Export (for llama.cpp)

```python
import subprocess
import os

def export_to_gguf(
    model_path: str,
    output_path: str,
    quantization: str = "q4_k_m"
):
    """
    Export model to GGUF format for llama.cpp inference.

    Quantization options:
    - q4_0, q4_1: Basic 4-bit
    - q4_k_s, q4_k_m: 4-bit with k-quants (recommended)
    - q5_0, q5_1, q5_k_s, q5_k_m: 5-bit variants
    - q8_0: 8-bit (highest quality)
    - f16: FP16 (no quantization)
    """
    llama_cpp_path = os.environ.get("LLAMA_CPP_PATH", "./llama.cpp")

    # Convert to GGUF
    convert_script = os.path.join(llama_cpp_path, "convert_hf_to_gguf.py")
    subprocess.run([
        "python", convert_script,
        model_path,
        "--outfile", f"{output_path}/model-f16.gguf",
        "--outtype", "f16"
    ], check=True)

    # Quantize
    quantize_binary = os.path.join(llama_cpp_path, "llama-quantize")
    subprocess.run([
        quantize_binary,
        f"{output_path}/model-f16.gguf",
        f"{output_path}/model-{quantization}.gguf",
        quantization
    ], check=True)

    # Clean up f16 file
    os.remove(f"{output_path}/model-f16.gguf")

    print(f"GGUF model saved: {output_path}/model-{quantization}.gguf")

# Usage
# export_to_gguf("./merged-model", "./gguf-output", "q4_k_m")
```

### Quantization Comparison

| Format | Size (8B model) | Speed | Quality | Use Case |
|--------|-----------------|-------|---------|----------|
| FP16 | ~16 GB | Baseline | 100% | Development, fine-tuning |
| GPTQ 4-bit | ~4 GB | ~1.5x | 98-99% | GPU inference |
| AWQ 4-bit | ~4 GB | ~1.8x | 98-99% | GPU inference (faster) |
| GGUF Q4_K_M | ~4.5 GB | ~2x | 97-98% | CPU + GPU, llama.cpp |
| GGUF Q5_K_M | ~5.5 GB | ~1.8x | 99% | Higher quality needs |

## Inference Optimization

### vLLM Deployment

```python
from vllm import LLM, SamplingParams

def deploy_with_vllm(
    model_path: str,
    tensor_parallel_size: int = 1,
    max_model_len: int = 4096,
    gpu_memory_utilization: float = 0.9
):
    """
    Deploy model with vLLM for high-throughput inference.

    vLLM provides:
    - Continuous batching
    - PagedAttention for efficient memory
    - Tensor parallelism for multi-GPU
    """
    llm = LLM(
        model=model_path,
        tensor_parallel_size=tensor_parallel_size,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        trust_remote_code=True,
        dtype="bfloat16"
    )

    return llm

def batch_inference_vllm(
    llm: LLM,
    prompts: list[str],
    max_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> list[str]:
    """Run batch inference with vLLM."""
    sampling_params = SamplingParams(
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p
    )

    outputs = llm.generate(prompts, sampling_params)

    return [output.outputs[0].text for output in outputs]

# Usage
# llm = deploy_with_vllm("./merged-model", tensor_parallel_size=2)
# responses = batch_inference_vllm(llm, ["Hello, how are you?", "What is AI?"])
```

### vLLM OpenAI-Compatible Server

```bash
# Start vLLM server with OpenAI-compatible API
python -m vllm.entrypoints.openai.api_server \
    --model ./merged-model \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 2 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9
```

```python
# Client usage
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")

response = client.chat.completions.create(
    model="./merged-model",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=256
)
print(response.choices[0].message.content)
```

### Text Generation Inference (TGI)

```yaml
# docker-compose.yml for TGI
version: "3.9"
services:
  tgi:
    image: ghcr.io/huggingface/text-generation-inference:latest
    ports:
      - "8080:80"
    volumes:
      - ./model:/data
    environment:
      - MODEL_ID=/data
      - NUM_SHARD=2
      - MAX_INPUT_LENGTH=2048
      - MAX_TOTAL_TOKENS=4096
      - QUANTIZE=bitsandbytes-nf4
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]
```

```python
# TGI client usage
from huggingface_hub import InferenceClient

client = InferenceClient("http://localhost:8080")

response = client.text_generation(
    prompt="Hello, how are you?",
    max_new_tokens=256,
    temperature=0.7,
    do_sample=True
)
print(response)
```

## Production Deployment Patterns

### Model Server with FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from contextlib import asynccontextmanager
import asyncio
from typing import Optional

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    stop: Optional[list[str]] = None

class GenerationResponse(BaseModel):
    text: str
    tokens_generated: int
    finish_reason: str

# Global model reference
model = None
tokenizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer
    # Load model on startup
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        "./merged-model",
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained("./merged-model")
    print("Model loaded!")
    yield
    # Cleanup on shutdown
    del model, tokenizer
    torch.cuda.empty_cache()

app = FastAPI(lifespan=lifespan)

@app.post("/generate", response_model=GenerationResponse)
async def generate(request: GenerationRequest):
    inputs = tokenizer(request.prompt, return_tensors="pt").to(model.device)

    # Run generation in thread pool to not block event loop
    loop = asyncio.get_event_loop()
    outputs = await loop.run_in_executor(
        None,
        lambda: model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            do_sample=request.temperature > 0,
            pad_token_id=tokenizer.pad_token_id
        )
    )

    generated_text = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True
    )

    return GenerationResponse(
        text=generated_text,
        tokens_generated=len(outputs[0]) - inputs["input_ids"].shape[1],
        finish_reason="length" if len(outputs[0]) >= request.max_tokens else "stop"
    )

@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": model is not None}
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-inference
spec:
  replicas: 2
  selector:
    matchLabels:
      app: llm-inference
  template:
    metadata:
      labels:
        app: llm-inference
    spec:
      containers:
        - name: llm
          image: your-registry/llm-server:latest
          ports:
            - containerPort: 8000
          resources:
            requests:
              nvidia.com/gpu: 1
              memory: "32Gi"
              cpu: "4"
            limits:
              nvidia.com/gpu: 1
              memory: "48Gi"
              cpu: "8"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 120
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 60
            periodSeconds: 10
          volumeMounts:
            - name: model-cache
              mountPath: /models
      volumes:
        - name: model-cache
          persistentVolumeClaim:
            claimName: model-pvc
      nodeSelector:
        nvidia.com/gpu.product: NVIDIA-A100-SXM4-80GB
---
apiVersion: v1
kind: Service
metadata:
  name: llm-inference
spec:
  selector:
    app: llm-inference
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
```

## Performance Benchmarking

```python
import time
import torch
from statistics import mean, stdev

def benchmark_inference(
    model,
    tokenizer,
    prompts: list[str],
    max_tokens: int = 256,
    warmup_runs: int = 3,
    benchmark_runs: int = 10
) -> dict:
    """
    Benchmark model inference performance.

    Returns latency, throughput, and memory metrics.
    """
    model.eval()

    # Warmup
    print("Warming up...")
    for _ in range(warmup_runs):
        inputs = tokenizer(prompts[0], return_tensors="pt").to(model.device)
        with torch.no_grad():
            model.generate(**inputs, max_new_tokens=max_tokens)

    # Clear cache
    torch.cuda.synchronize()
    torch.cuda.empty_cache()

    # Benchmark
    latencies = []
    tokens_generated = []

    print("Benchmarking...")
    for prompt in prompts[:benchmark_runs]:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        input_len = inputs["input_ids"].shape[1]

        torch.cuda.synchronize()
        start_time = time.perf_counter()

        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=max_tokens)

        torch.cuda.synchronize()
        end_time = time.perf_counter()

        latency = end_time - start_time
        num_tokens = outputs.shape[1] - input_len

        latencies.append(latency)
        tokens_generated.append(num_tokens)

    # Memory stats
    memory_allocated = torch.cuda.max_memory_allocated() / 1024**3
    memory_reserved = torch.cuda.max_memory_reserved() / 1024**3

    avg_latency = mean(latencies)
    avg_tokens = mean(tokens_generated)

    return {
        "avg_latency_ms": avg_latency * 1000,
        "latency_std_ms": stdev(latencies) * 1000 if len(latencies) > 1 else 0,
        "avg_tokens_per_second": avg_tokens / avg_latency,
        "throughput_requests_per_second": 1 / avg_latency,
        "memory_allocated_gb": memory_allocated,
        "memory_reserved_gb": memory_reserved
    }

# Usage
# metrics = benchmark_inference(model, tokenizer, test_prompts)
# print(f"Latency: {metrics['avg_latency_ms']:.1f}ms")
# print(f"Throughput: {metrics['avg_tokens_per_second']:.1f} tokens/s")
```

## Quick Reference

### Deployment Decision Tree

```
Is latency critical (<100ms)?
├── Yes → Use vLLM with tensor parallelism
└── No
    ├── Is batch throughput priority?
    │   ├── Yes → Use vLLM or TGI
    │   └── No → Standard HF inference is fine
    └── Is memory constrained?
        ├── Yes → Use GGUF + llama.cpp or AWQ
        └── No → Use FP16 or GPTQ
```

### Quantization Selection

| Priority | Recommended Format |
|----------|-------------------|
| Maximum quality | FP16 (no quantization) |
| Best quality/size tradeoff | AWQ 4-bit or GGUF Q5_K_M |
| Minimum size | GGUF Q4_K_S or GPTQ 4-bit |
| CPU inference | GGUF Q4_K_M |
| Multi-GPU scaling | vLLM with FP16 or AWQ |

## Related References

- `lora-peft.md` - Adapter merging strategies
- `evaluation-metrics.md` - Post-deployment evaluation
- `hyperparameter-tuning.md` - Training configurations
