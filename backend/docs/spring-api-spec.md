# Spring API Spec

This document fixes the MVP API contract between Flutter and Spring.
The current AI service is photo-based. Flutter should call Spring only; Spring calls the FastAPI AI service asynchronously after a fitting request is created.

## Common Rules

- Base URL: `http://<spring-host>:8080`
- Protected APIs require `Authorization: Bearer <token>`.
- The token is currently a JWT returned by the mock login API.
- Final 3D result URL is `avatarGlbUrl`, not `resultSplatUrl`.
- User input source is a single image, so use `sourceImageUrl`, not `sourceVideoUrl`.

## 1. Mock Login

### Request

`POST /api/auth/google`

Content-Type: `application/x-www-form-urlencoded`

| field | type | required |
| --- | --- | --- |
| email | string | yes |
| name | string | yes |

### Response

```json
{
  "token": "jwt-token",
  "userId": 1,
  "email": "test@example.com",
  "name": "Test User",
  "heightCm": 178.0
}
```

## 2. Save My Height

### Request

`PUT /api/users/me/body-info`

Headers:

`Authorization: Bearer <token>`

Body:

```json
{
  "heightCm": 178.0
}
```

### Response

```json
{
  "userId": 1,
  "heightCm": 178.0
}
```

Behavior:

- Updates `users.height_cm`.
- Upserts `user_measurements.height_cm` for the same user.

## 2-1. Upload My Source Image

### Request

`POST /api/users/me/source-image`

Headers:

`Authorization: Bearer <token>`

Content-Type: `multipart/form-data`

| field | type | required |
| --- | --- | --- |
| file | image file | yes |

### Response

```json
{
  "id": 1,
  "userId": 1,
  "heightCm": 178.0,
  "shoulderWidthCm": null,
  "chestWidthCm": null,
  "sleeveLengthCm": null,
  "waistWidthCm": null,
  "hipWidthCm": null,
  "thighWidthCm": null,
  "crotchCm": null,
  "sourceImageUrl": "/storage/measurements/1/source-images/uuid_input.jpg",
  "smplMeshUrl": null,
  "resultJsonUrl": null
}
```

Behavior:

- Saves the uploaded image into local storage.
- Stores the returned `/storage/...` URL in `user_measurements.source_image_url`.
- Requires height to be saved first because `user_measurements.height_cm` is not nullable.
- This is the image path Spring later passes to the FastAPI AI service.

## 3. Get Clothes List

### Request

`GET /api/clothes`

Auth is not required.

### Response

```json
[
  {
    "id": 1,
    "name": "White T-Shirt",
    "category": "TOP",
    "imageUrl": "/storage/clothes/top.png",
    "base3dUrl": "/storage/clothes/top.glb",
    "totalLengthCm": 69.0,
    "shoulderWidthCm": 50.0,
    "chestWidthCm": 58.0,
    "sleeveLengthCm": 23.0,
    "waistWidthCm": null,
    "hipWidthCm": null,
    "thighWidthCm": null,
    "crotchCm": null,
    "hemWidthCm": null
  }
]
```

Current categories:

- `TOP`
- `BOTTOM`

`OUTER` is excluded from the current MVP scope.

## 4. Create Fitting History

### Request

`POST /api/fitting/history`

Headers:

`Authorization: Bearer <token>`

Body:

```json
{
  "clothesId": 1
}
```

### Response

```json
{
  "fittingId": 10,
  "clothesId": 1,
  "status": "PENDING",
  "message": "Fitting request created successfully."
}
```

Current behavior:

- Creates a row in `fitting_histories`.
- Initial status is `PENDING`.
- Starts the FastAPI AI fitting job asynchronously after the DB transaction commits.
- While AI is running, the status can become `PROCESSING`.
- On success, Spring stores `aiJobId`, `avatarGlbUrl`, `renderImageUrl`, and `resultJsonUrl`.
- On failure, Spring updates the status to `FAIL`.

## 5. Get Fitting History

### Request

`GET /api/fitting/history`

Headers:

`Authorization: Bearer <token>`

### Response

```json
[
  {
    "id": 10,
    "clothesId": 1,
    "clothesName": "White T-Shirt",
    "fittingDate": "2026-05-31",
    "createdAt": "2026-05-31T17:30:00",
    "status": "SUCCESS",
    "aiJobId": "sample-ai-job-001",
    "avatarGlbUrl": "http://localhost:8000/outputs/sample-ai-job-001/avatar.glb",
    "renderImageUrl": "http://localhost:8000/outputs/sample-ai-job-001/render_front.png",
    "resultJsonUrl": "http://localhost:8000/outputs/sample-ai-job-001_result.json"
  }
]
```

Status values:

- `PENDING`
- `PROCESSING`
- `SUCCESS`
- `FAIL`

## 6. Get Fitting Status

### Request

`GET /api/fitting/history/{fittingId}`

Headers:

`Authorization: Bearer <token>`

### Response

```json
{
  "id": 10,
  "clothesId": 1,
  "clothesName": "White T-Shirt",
  "fittingDate": "2026-05-31",
  "createdAt": "2026-05-31T17:30:00",
  "status": "PROCESSING",
  "aiJobId": "sample-ai-job-001",
  "avatarGlbUrl": null,
  "renderImageUrl": null,
  "resultJsonUrl": null
}
```

Current behavior:

- Returns one fitting history row owned by the authenticated user.
- Use this endpoint for Flutter polling after `POST /api/fitting/history`.
- Other users cannot read this fitting history by ID.

## 7. Get Fitting Result

### Request

`GET /api/fitting/history/{fittingId}/result`

Headers:

`Authorization: Bearer <token>`

### Response

```json
{
  "fittingId": 10,
  "status": "SUCCESS",
  "ready": true,
  "aiJobId": "sample-ai-job-001",
  "avatarGlbUrl": "/outputs/sample-ai-job-001/avatar.glb",
  "renderImageUrl": "/outputs/sample-ai-job-001/render_front.png",
  "resultJsonUrl": "/outputs/sample-ai-job-001_result.json",
  "message": "피팅 결과가 준비되었습니다."
}
```

Current behavior:

- Returns only the fields needed by the Flutter result screen.
- `ready` is `true` only when status is `SUCCESS` and `avatarGlbUrl` exists.
- If AI processing failed, status is `FAIL` and result URLs can be `null`.
- Other users cannot read this fitting result by ID.

## 8. AI Result JSON Contract

Spring should normalize the FastAPI AI result into this shape before saving DB fields.
The same example is stored at `backend/docs/ai-result-example.json`.

### FastAPI source endpoints

```text
POST /api/fit
GET  /api/job/{job_id}
GET  /api/measurements/{job_id}
GET  /api/avatar-glb/{job_id}
GET  /api/renders/{job_id}
```

### Canonical AI result example

```json
{
  "job_id": "sample-ai-job-001",
  "status": "done",
  "measurements_cm": {
    "height_cm": 178.0,
    "shoulder_width_cm": 47.2,
    "chest_width_cm": 52.0,
    "sleeve_length_cm": 58.3,
    "waist_width_cm": 41.0,
    "hip_width_cm": 50.5,
    "thigh_width_cm": 28.4,
    "crotch_cm": 73.2
  },
  "smpl_mesh_url": "/outputs/debug/sample-ai-job-001/smplx.ply",
  "avatar_glb_url": "/outputs/sample-ai-job-001/avatar.glb",
  "shirt_glb_url": "/outputs/sample-ai-job-001/shirt_fitted.glb",
  "pants_glb_url": "/outputs/sample-ai-job-001/pants_fitted.glb",
  "render_urls": [
    "/outputs/sample-ai-job-001/render_front.png",
    "/outputs/sample-ai-job-001/render_side.png"
  ],
  "result_json_url": "/outputs/sample-ai-job-001_result.json"
}
```

### Spring DB mapping

| AI result field | Spring DB field |
| --- | --- |
| `job_id` | `fitting_histories.ai_job_id` |
| `measurements_cm.height_cm` | `user_measurements.height_cm` |
| `measurements_cm.shoulder_width_cm` | `user_measurements.shoulder_width_cm` |
| `measurements_cm.chest_width_cm` | `user_measurements.chest_width_cm` |
| `measurements_cm.sleeve_length_cm` | `user_measurements.sleeve_length_cm` |
| `measurements_cm.waist_width_cm` | `user_measurements.waist_width_cm` |
| `measurements_cm.hip_width_cm` | `user_measurements.hip_width_cm` |
| `measurements_cm.thigh_width_cm` | `user_measurements.thigh_width_cm` |
| `measurements_cm.crotch_cm` | `user_measurements.crotch_cm` |
| uploaded image URL from Spring | `user_measurements.source_image_url` |
| `smpl_mesh_url` | `user_measurements.smpl_mesh_url` |
| `result_json_url` | `user_measurements.result_json_url`, `fitting_histories.result_json_url` |
| `avatar_glb_url` | `fitting_histories.avatar_glb_url` |
| first item of `render_urls` | `fitting_histories.render_image_url` |

### Notes

- `result_splat_url` is removed from the current MVP contract.
- `shirt_glb_url` and `pants_glb_url` are optional AI artifact fields and are not stored in the current ERD.
- If the FastAPI response uses snake_case, Spring DTOs should parse snake_case and expose camelCase to Flutter.
- If AI returns relative paths, Spring should prefix the configured AI base URL before saving or returning them.
