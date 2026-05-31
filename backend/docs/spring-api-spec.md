# Spring API Spec

This document fixes the MVP API contract between Flutter and Spring.
AI service integration and DB detail changes can be added later, but Flutter should use only these endpoints for now.

## Common Rules

- Base URL: `http://<spring-host>:8080`
- Protected APIs require `Authorization: Bearer <token>`.
- The token is currently a JWT returned by the mock login API.

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
- Does not call the AI service yet.
- Initial status is `PENDING`.

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
    "status": "PENDING",
    "resultSplatUrl": null
  }
]
```

Status values:

- `PENDING`
- `PROCESSING`
- `SUCCESS`
- `FAIL`

`resultSplatUrl` is intentionally kept for the current ERD. It can be renamed later if final output becomes OBJ/GLB/image centered.