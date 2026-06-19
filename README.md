# Fit360 — AI-Based 3D Virtual Fitting & Body Analysis System
> **A personalized 3D virtual fitting platform built from a single full-body smartphone photo and your real height**

This project generates an **SMPL-X 3D human mesh** from a user's full-body photo and real height, compares the garment's **actual measurements and the user's body shape** to determine whether it fits, and lets the user view the clothed **3D avatar** in a mobile app. Python generates the 3D human mesh and body measurements, Spring Boot powers the backend API, and Flutter implements the mobile interface.

<img width="2200" height="1440" alt="Image" src="https://github.com/user-attachments/assets/50cf0f3e-e660-4fbb-98b1-7dc4f6f81e13" />

---

## Background

### 1. Limitations of Online Clothing Shopping
* **No try-on:** Hard to judge fit, length, ease, and how well a garment suits your body in advance
* **Frequent returns:** Wrong size selection leads to constant returns and exchanges → consumer inconvenience + higher seller logistics costs
* **Environmental burden:** Repeated shipping and returns drive packaging waste and discarded clothing

### 2. Limitations of Existing 2D Virtual Fitting
* **Simple image overlay:** Stays at the level of pasting a clothing image on top of a photo
* **No depth:** Fails to reflect garment thickness/volume, the side and back views, or body-specific ease
* **No measurements:** Cannot evaluate the relationship to actual body dimensions such as shoulders, waist, and hips

### 3. Limitations of Body-Measurement Equipment
* **Dependence on expensive hardware:** Precise body measurement requires dedicated 3D scanners
* **Low accessibility:** Ordinary users cannot easily measure and apply their body data
* **→ Our solution:** A practical system that performs body analysis + virtual fitting from a smartphone photo alone

<br/>

## Tech Stack

| Category | Technology |
| :--- | :--- |
| **Frontend** | ![Flutter](https://img.shields.io/badge/Flutter-02569B?style=flat&logo=flutter&logoColor=white) ![Dart](https://img.shields.io/badge/Dart-3.11-0175C2?style=flat&logo=dart&logoColor=white) ![model-viewer](https://img.shields.io/badge/model__viewer-3D_Viewer-FF6F00?style=flat) |
| **Backend** | ![Java](https://img.shields.io/badge/Java-17-007396?style=flat&logo=openjdk&logoColor=white) ![SpringBoot](https://img.shields.io/badge/Spring_Boot-4.0-6DB33F?style=flat&logo=spring-boot&logoColor=white) ![Spring Security](https://img.shields.io/badge/Spring_Security-6DB33F?style=flat&logo=spring-security&logoColor=white) ![JPA](https://img.shields.io/badge/JPA-Hibernate-59666C?style=flat&logo=hibernate&logoColor=white) ![JWT](https://img.shields.io/badge/JWT-JSON_Web_Token-000000?style=flat&logo=json-web-tokens&logoColor=white) |
| **AI Server** | ![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![SMPL-X](https://img.shields.io/badge/SMPL--X-Human_Model-FF6F00?style=flat) ![MediaPipe](https://img.shields.io/badge/MediaPipe-0097A7?style=flat&logo=google&logoColor=white) ![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white) |
| **3D** | ![Blender](https://img.shields.io/badge/Blender-F5792A?style=flat&logo=blender&logoColor=white) ![trimesh](https://img.shields.io/badge/trimesh-3D_Mesh-59666C?style=flat) ![glTF](https://img.shields.io/badge/glTF-GLB-87B741?style=flat) |
| **Database** | ![MariaDB](https://img.shields.io/badge/MariaDB-003545?style=flat&logo=mariadb&logoColor=white) |
| **Tools** | ![IntelliJ](https://img.shields.io/badge/IntelliJ_IDEA-000000?style=flat&logo=intellij-idea&logoColor=white) ![VS Code](https://img.shields.io/badge/VS_Code-007ACC?style=flat&logo=visual-studio-code&logoColor=white) ![DBeaver](https://img.shields.io/badge/DBeaver-372923?style=flat&logo=dbeaver&logoColor=white) ![Postman](https://img.shields.io/badge/Postman-FF6C37?style=flat&logo=postman&logoColor=white) |
| **Collaboration** | ![Git](https://img.shields.io/badge/Git-F05032?style=flat&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white) ![Discord](https://img.shields.io/badge/Discord-5865F2?style=flat&logo=discord&logoColor=white) |

<br/>

## System Design

**[Use Case Diagram]**

![유스케이스](images/usecase.png)

**[ERD]**

![ERD](images/erd.png)

<br/>

## Project Structure 

 **Frontend (Flutter)**, **Backend (Spring Boot)**, and **AI Server (Python)**.A monorepo with separated

```bash
AI-based-3D-Virtual-Fitting/
├── ai-service/              # Python AI processing server (FastAPI, port 8000)
│   ├── main.py              # API entry point (/api/fit, /api/job, /api/measurements ...)
│   ├── core/                # Pipeline (step1~5, merge_glb, measure_body ...)
│   ├── blender_scripts/     # Headless Blender cloth simulation
│   ├── clothes/             # Clothing library (GLB, thumbnails, catalog.json)
│   └── weights/             # SMPL-X weights (downloaded separately, not in repo)
│
├── backend/                 # Spring Boot API server (port 8080)
│   └── src/main/java/.../virtualfitting/
│       ├── domain/{user, clothes, fitting, measurement}/   # Per-domain layers
│       └── global/{security, error, infra, config}/        # JWT, exceptions, file storage
│
├── frontend/                # Flutter mobile app
│   └── lib/
│       ├── core/            # Shared API client, token, config, state
│       └── features/{auth, home, clothes, fitting, profile, scan, settings}/
│
└── README.md
```

<br/>

## Key Features

### 1. Photo-Based 3D Human Mesh Generation
Creates a personalized 3D avatar from a single full-body photo and the user's real height.
* **Pose analysis:** Extracts body and face landmarks with MediaPipe
* **Body-shape fitting:** Represents body shape via SMPL-X parameters (betas), with scale correction using the real height

### 2. Real Body Measurement
Extracts the key dimensions needed for garment fitting from the SMPL-X mesh, in centimeters.
* **Measured items:** Shoulder width, chest width, waist width, hip width, thigh width, sleeve length, rise
* **Usage:** Saved as JSON for retrieval by the server/app and used in fit decisions

### 3. Virtual Fitting & Fit Decision
* **Fit decision:** Compares the garment's actual measurements against body dimensions to flag fit/no-fit
* **3D garment alignment:** Fits clothing to the body via Blender cloth simulation, applies a solid (representative) color, and merges into a single GLB
* **Default outfit:** When no top/bottom is selected, a default short-sleeve top and shorts are applied automatically

### 4. Mobile App & Authentication
* **3D viewer:** Rotate and zoom the clothed avatar (model-viewer)
* **Authentication:** Email/password sign-up and login (BCrypt + JWT), with per-account data isolation

## Demo

**[Login / Clothing List / Fitting History]**

<img src="images/demo_login.png" width="32%"/> <img src="images/demo_clothes.png" width="32%"/> <img src="images/demo_history.png" width="32%"/>

**[Fit Decision]** — Compares garment measurements against body shape to indicate fit (left) / no-fit (right)

<img src="images/demo_fit_ok.png" width="40%"/> <img src="images/demo_fit_no.png" width="40%"/>

**[3D Fitting Result]** — Rotate and zoom the clothed avatar

<img src="images/demo_result_front.png" width="40%"/> <img src="images/demo_result_side.png" width="40%"/>

<br/>

## Getting Started

### 1. Run the AI Server (FastAPI)
```bash
cd ai-service
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt
python main.py
```
> The SMPL-X weights (`weights/smplx/...`) are licensed assets and are not included in the repo → download them from the [official site](https://smpl-x.is.tue.mpg.de/) and place them accordingly. **Blender** is required for the garment cloth simulation. Health check: http://localhost:8000

### 2. Run the Backend (Spring Boot)
```bash
cd backend
gradlew bootRun
```
> MariaDB must be running (the schema is auto-created via `ddl-auto=update`). Environment variables: `DB_URL`, `DB_USERNAME`, `DB_PASSWORD`, `JWT_SECRET`, `AI_SERVICE_BASE_URL` (internal), `AI_SERVICE_PUBLIC_BASE_URL` (mobile access). Health check: http://localhost:8080

### 3. Run the Frontend (Flutter)
```bash
cd frontend
flutter pub get
flutter run
```
> Set the backend address in the app's "Server Address Settings" or in `lib/core/config/api_config.dart` (use your PC's LAN/hotspot IP for physical devices).


<br/>

## Team Members & Roles

| Name | Position | Responsibilities |
| :--- | :--- | :--- |
| **Lee Seungmin** (Lead) | Backend | • Design & implementation of the Spring Boot REST API server<br>• DB modeling for users, clothing, body measurements, and fitting history (JPA)<br>• JWT authentication & garment fit decision logic<br>• Data relay between Flutter ↔ Python AI server |
| **Choi Yeseong** | Frontend | • Design & implementation of the Flutter mobile app UI/UX<br>• Login, height input, clothing list, and fitting history screens<br>• GLB 3D avatar viewer integration<br>• Spring Boot API integration |
| **Kwak Donghyun** | AI | • SMPL-X-based 3D human mesh generation & scale correction<br>• Extraction of body dimensions (shoulders, chest, waist, hips, etc.)<br>• Garment alignment via Blender cloth simulation<br>• JSON & 3D (GLB) result output |


> Dong-eui University, Dept. of Computer Software · Capstone Design · Advisor: Prof. Kwon Soon-gak · Fitting Team
