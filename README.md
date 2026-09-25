# Toru

**Autonomous AI Social Media Agent**

Toru is an autonomous AI agent that plans, creates, renders, schedules, and publishes short-form content to Instagram.

The agent operates across configurable content domains, currently focused on **Technology, Artificial Intelligence, and Aviation**, and runs continuously in the cloud without requiring manual content creation or a local machine to stay online.

## What Toru Does

- Plans topics and prepares upcoming content autonomously
- Generates scripts, captions, and speech using AI
- Converts speech into word-level timing data for synchronized animation and subtitles
- Renders a custom 2D presenter through a deterministic animation engine
- Composes production-ready vertical videos with FFmpeg
- Schedules and publishes Reels automatically through the Instagram Graph API
- Persists content and job state to recover from service restarts
- Runs continuously as a containerized cloud application

## Architecture

```text
Topic Planning
      |
      v
Script & Caption Generation
      |
      v
OpenAI TTS
      |
      v
Whisper Transcription
      |
      v
Toru 2D Animation Engine
      |
      v
FFmpeg Composition
      |
      v
Cloudinary
      |
      v
Scheduled Instagram Publishing


PostgreSQL <---- Application State
Redis / RQ <---- Background Jobs
Docker     <---- Service Orchestration
```

## Engineering Highlights

### Autonomous Content Pipeline

Toru handles the complete lifecycle of a Reel, from topic selection to publishing. Content is planned and rendered ahead of its publishing time, allowing the system to operate without manual intervention.

### Deterministic 2D Rendering

The original generative-video approach was replaced with a custom 2D animation engine. This keeps Toru's visual identity consistent, makes video generation predictable, and reduces recurring generation costs.

### Decoupled Background Processing

Video generation and publishing use separate **Redis/RQ queues**, preventing CPU-intensive rendering jobs from blocking time-sensitive publishing tasks.

### Persistent Scheduling

Content, media, and scheduling state are stored in **PostgreSQL**. Incomplete future Reel jobs can be recovered after service restarts, improving reliability for continuous operation.

## Tech Stack

**Core:** Python, FastAPI, PostgreSQL, Redis/RQ

**AI:** OpenAI APIs, Text-to-Speech, Whisper

**Media:** FFmpeg, Custom 2D Animation Engine, Cloudinary

**Infrastructure:** Docker, Docker Compose, Oracle Cloud

**Publishing:** Instagram Graph API

## Deployment

Toru runs as a multi-service Docker application on an ARM64 Oracle Cloud instance.

```text
Planner
   |
   v
Redis/RQ ---> Reel Worker
   |
   +-------> Publish Worker
                 ^
                 |
             Scheduler

        PostgreSQL
```

The production system is designed to generate content in advance and publish **two Reels per day** according to its configured schedule.

## Running Locally

Clone the repository and create the environment configuration:

```bash
git clone https://github.com/denizzsarierr/lazy-socialmedia-agent.git
cd lazy-socialmedia-agent

cp .env.example .env
```

Add the required OpenAI, Cloudinary, Instagram, PostgreSQL, and Redis configuration to `.env`, then start the stack:

```bash
docker compose up -d --build
```

Check the services:

```bash
docker compose ps
```

## Status

The complete autonomous pipeline is operational:

```text
Plan -> Generate -> Speak -> Transcribe -> Animate -> Render -> Schedule -> Publish
```

Toru is currently deployed for continuous cloud operation with automated content generation and scheduled Instagram publishing.