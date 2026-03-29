package com.grabpic.backend.service;

import com.grabpic.backend.dto.SearchResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
@RequiredArgsConstructor
public class EventService {

  private final AiService aiService;

  // -------------------------
  // PROCESS IMAGES
  // -------------------------
  public String processImages(String eventId, MultipartFile[] files) {
    validateFiles(files);
    return aiService.processImages(eventId, files);
  }

  // -------------------------
  // SEARCH IMAGES (UPDATED)
  // -------------------------
  public SearchResponse searchImages(String eventId, MultipartFile[] files, int page, int size) {
    validateFiles(files);
    return aiService.searchImages(eventId, files, page, size);
  }


  // -------------------------
  // VALIDATION
  // -------------------------
  private void validateFiles(MultipartFile[] files) {
    if (files == null || files.length == 0) {
      throw new RuntimeException("No files provided");
    }
  }
  public byte[] downloadAll(String eventId) {
    return aiService.downloadAllImages(eventId);
  }
}
