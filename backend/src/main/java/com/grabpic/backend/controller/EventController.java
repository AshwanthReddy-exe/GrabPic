package com.grabpic.backend.controller;

import com.grabpic.backend.dto.SearchResponse;
import com.grabpic.backend.service.EventService;
import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/events")
@RequiredArgsConstructor
public class EventController {

  private final EventService eventService;

  // -------------------------
  // CREATE EVENT
  // -------------------------
  @PostMapping
  public ResponseEntity<Map<String, String>> createEvent() {
    String eventId = UUID.randomUUID().toString();
    return ResponseEntity.ok(Map.of("eventId", eventId));
  }

  // -------------------------
  // UPLOAD IMAGES
  // -------------------------
  @PostMapping("/{eventId}/upload")
  public ResponseEntity<String> uploadImages(
      @PathVariable String eventId,
      @RequestParam("files") MultipartFile[] files) {
    String result = eventService.processImages(eventId, files);
    return ResponseEntity.ok(result);
  }

  // -------------------------
  // SEARCH IMAGES
  // -------------------------
  @PostMapping("/{eventId}/search")
  public ResponseEntity<SearchResponse> searchImages(
      @PathVariable String eventId,
      @RequestParam("files") MultipartFile[] files,
      @RequestParam(defaultValue = "1") int page,
      @RequestParam(defaultValue = "20") int size) {

    SearchResponse response = eventService.searchImages(eventId, files, page, size);
    return ResponseEntity.ok(response);
  }

  // -------------------------
  // FETCH IMAGE (PROXY)
  // -------------------------
  @GetMapping("/{eventId}/images/{imageId}")
  public ResponseEntity<byte[]> getImage(
      @PathVariable String eventId,
      @PathVariable String imageId) {
    byte[] image = eventService.fetchImage(eventId, imageId);

    return ResponseEntity
        .ok()
        .contentType(MediaType.IMAGE_JPEG)
        .body(image);
  }

  @GetMapping("/{eventId}/download")
  public ResponseEntity<byte[]> downloadAll(@PathVariable String eventId) {

    byte[] zip = eventService.downloadAll(eventId);

    return ResponseEntity.ok()
        .header(HttpHeaders.CONTENT_DISPOSITION,
            "attachment; filename=\"photos.zip\"")
        .contentType(MediaType.APPLICATION_OCTET_STREAM)
        .body(zip);
  }
}
