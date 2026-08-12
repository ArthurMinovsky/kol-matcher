FROM langflowai/langflow:1.11.0

USER root
RUN pip install --no-cache-dir httpx

COPY components/ /app/custom_components/
COPY flows/ /app/flows/

ENV LANGFLOW_COMPONENTS_PATH=/app/custom_components
ENV PYTHONPATH=/app/custom_components
