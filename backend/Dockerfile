# ---------- build stage (.NET) ----------
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy csproj first for better layer caching
COPY backend/Parser.Application/Parser.Application.csproj backend/Parser.Application/
COPY backend/Parser.Api/Parser.Api.csproj backend/Parser.Api/
RUN dotnet restore backend/Parser.Api/Parser.Api.csproj

# Copy the rest and publish
COPY backend/ backend/
RUN dotnet publish backend/Parser.Api/Parser.Api.csproj -c Release -o /app/publish

# ---------- runtime stage ----------
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app

# Install python + venv support (PEP 668 friendly)
RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 python3-venv python3-pip \
  && rm -rf /var/lib/apt/lists/*

# Copy .NET published output from the build stage
COPY --from=build /app/publish/ ./

# Copy python code (and data)
COPY aiparser/ /app/aiparser/

# Create venv + install deps into it
RUN python3 -m venv /opt/venv \
  && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
  && /opt/venv/bin/pip install --no-cache-dir -r /app/aiparser/requirements.txt

# Ensure python can import aiparser
ENV PYTHONPATH=/app
ENV PATH="/opt/venv/bin:$PATH"

# ASP.NET
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080

ENTRYPOINT ["dotnet", "Parser.Api.dll"]
