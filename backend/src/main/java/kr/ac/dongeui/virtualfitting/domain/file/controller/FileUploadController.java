package kr.ac.dongeui.virtualfitting.domain.file.controller;

import kr.ac.dongeui.virtualfitting.global.infra.file.LocalFileStorageService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;

/**
 * S3 ?? ?? ???? ??? ???? ??? API? ????.
 */
@RestController
@RequestMapping("/api/files")
public class FileUploadController {

    private final LocalFileStorageService localFileStorageService;

    public FileUploadController(LocalFileStorageService localFileStorageService) {
        this.localFileStorageService = localFileStorageService;
    }

    /**
     * ???? ??? ?? ??? ???? ?????? ?? ??? URL? ????.
     */
    @PostMapping("/upload")
    public ResponseEntity<Map<String, String>> uploadFile(
            @RequestParam("file") MultipartFile file,
            @RequestParam("folder") String folder) {

        try {
            String fileUrl = localFileStorageService.uploadFile(file, folder);
            return ResponseEntity.ok(Map.of(
                    "message", "File uploaded successfully.",
                    "fileUrl", fileUrl
            ));
        } catch (IOException e) {
            return ResponseEntity.internalServerError().body(Map.of("error", "File upload failed."));
        }
    }
}
