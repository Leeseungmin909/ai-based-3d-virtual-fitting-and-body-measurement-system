package kr.ac.dongeui.virtualfitting.domain.fitting.entity;

public enum FittingStatus {
    PENDING,     // Spring에서 피팅 요청을 접수하고 AI 작업 시작을 기다리는 상태
    PROCESSING,  // FastAPI가 아바타와 의상 피팅 결과를 생성하는 상태
    SUCCESS,     // avatar GLB와 렌더 이미지 URL 발급이 완료된 상태
    FAIL         // AI 호출 또는 피팅 처리 실패 상태
}