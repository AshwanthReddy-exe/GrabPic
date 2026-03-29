package com.grabpic.backend.service;

import com.grabpic.backend.config.AiProperties;
import com.grabpic.backend.dto.ImageMatch;
import com.grabpic.backend.dto.SearchResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.core.ParameterizedTypeReference;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import com.azure.storage.blob.*;
import com.azure.storage.blob.sas.*;
import jakarta.annotation.PostConstruct;
import java.time.OffsetDateTime;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class AiService {

  private final RestTemplate restTemplate;
  private final AiProperties aiProperties;
  private final TokenService tokenService;
  private BlobServiceClient blobServiceClient;

  @PostConstruct
  public void init() {
    if (aiProperties.isUseBlobStorage() && 
        aiProperties.getAzureStorageConnectionString() != null && 
        !aiProperties.getAzureStorageConnectionString().isEmpty()) {
      this.blobServiceClient = new BlobServiceClientBuilder()
          .connectionString(aiProperties.getAzureStorageConnectionString())
          .buildClient();
    }
  }

  // -------------------------
  // PROCESS
  // -------------------------
  public String processImages(String eventId, MultipartFile[] files) {
    String url = buildApiUrl("process", eventId);
    return sendMultipartRequest(url, files);
  }

  // -------------------------
  // SEARCH (WITH PAGINATION)
  // -------------------------
  public SearchResponse searchImages(String eventId, MultipartFile[] files, int page, int size) {

    String url = buildApiUrl("search", eventId);
    MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();

    try {
      for (MultipartFile file : files) {
        body.add("files", toResource(file));
      }

      HttpHeaders headers = new HttpHeaders();
      headers.setContentType(MediaType.MULTIPART_FORM_DATA);

      HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

      ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
          url,
          HttpMethod.POST,
          request,
          new ParameterizedTypeReference<Map<String, Object>>() {
          });

      MatchBuckets buckets = mapToBuckets(response.getBody(), eventId);
      return paginate(buckets, page, size);

    } catch (Exception e) {
      log.error("AI search failed for event {}", eventId, e);
      throw new RuntimeException("AI search failed", e);
    }
  }


  // -------------------------
  // DOWNLOAD ALL (ZIP)
  // -------------------------
  public byte[] downloadAllImages(String eventId) {
    try {
      String url = buildDownloadUrl(eventId);
      ResponseEntity<byte[]> response = restTemplate.getForEntity(url, byte[].class);
      return response.getBody();

    } catch (Exception e) {
      log.error("Download failed for event {}", eventId, e);
      throw new RuntimeException("Failed to download ZIP", e);
    }
  }

  // -------------------------
  // URL BUILDERS (FIXED)
  // -------------------------
  private String buildApiUrl(String endpoint, String eventId) {
    return String.format("%s/%s/%s",
        trimSlash(aiProperties.getInternalBaseUrl()),
        trimSlash(endpoint),
        eventId);
  }


  private String buildDownloadUrl(String eventId) {
    return String.format("%s/events/%s/download",
        trimSlash(aiProperties.getInternalBaseUrl()),
        eventId);
  }

  private String trimSlash(String value) {
    return value.replaceAll("^/|/$", "");
  }

  // -------------------------
  // HELPERS
  // -------------------------
  private String sendMultipartRequest(String url, MultipartFile[] files) {
    try {
      MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();

      for (MultipartFile file : files) {
        body.add("files", toResource(file));
      }

      HttpHeaders headers = new HttpHeaders();
      headers.setContentType(MediaType.MULTIPART_FORM_DATA);

      HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

      ResponseEntity<String> response = restTemplate.postForEntity(url, request, String.class);

      return response.getBody();

    } catch (Exception e) {
      log.error("AI call failed: {}", url, e);
      throw new RuntimeException("AI call failed", e);
    }
  }

  private ByteArrayResource toResource(MultipartFile file) throws Exception {
    return new ByteArrayResource(file.getBytes()) {
      @Override
      public String getFilename() {
        return file.getOriginalFilename();
      }
    };
  }

  // -------------------------
  // BUCKET HOLDER
  // -------------------------
  private static class MatchBuckets {
    List<ImageMatch> strong;
    List<ImageMatch> weak;

    MatchBuckets(List<ImageMatch> strong, List<ImageMatch> weak) {
      this.strong = strong;
      this.weak = weak;
    }
  }

  // -------------------------
  // MAP RAW → BUCKETS
  // -------------------------
  private MatchBuckets mapToBuckets(Map<String, Object> body, String eventId) {

    if (body == null) {
      throw new RuntimeException("Empty response from AI service");
    }

    if (body.containsKey("error")) {
      throw new RuntimeException("AI error: " + body.get("error"));
    }

    List<Map<String, Object>> strong = safeList(body.get("strong_matches"));
    List<Map<String, Object>> weak = safeList(body.get("weak_matches"));
    
    List<ImageMatch> strongMatches = strong.stream()
        .map(m -> buildImageMatch(m, eventId))
        .toList();

    List<ImageMatch> weakMatches = weak.stream()
        .map(m -> buildImageMatch(m, eventId))
        .toList();

    return new MatchBuckets(strongMatches, weakMatches);
  }

  private ImageMatch buildImageMatch(Map<String, Object> m, String eventId) {
    String imageId = (String) m.get("image_id");
    double score = ((Number) m.get("score")).doubleValue();

    if (aiProperties.isUseBlobStorage() && blobServiceClient != null) {
      return new ImageMatch(imageId, score, buildSasUrl(eventId, imageId));
    }

    // Fallback: Use AI service signed URLs
    long expiryTs = (System.currentTimeMillis() / 1000L) + (3 * 3600);
    String token = tokenService.generateToken(eventId, imageId, expiryTs);
    String url = String.format("%s/images/%s/images/%s?token=%s",
        trimSlash(aiProperties.getPublicBaseUrl()),
        eventId,
        imageId,
        token);
    return new ImageMatch(imageId, score, url);
  }

  private String buildSasUrl(String eventId, String imageId) {
    try {
      String blobPath = String.format("events/%s/images/%s", eventId, imageId);
      BlobClient blobClient = blobServiceClient
          .getBlobContainerClient(aiProperties.getAzureContainerName())
          .getBlobClient(blobPath);

      BlobSasPermission permission = new BlobSasPermission().setReadPermission(true);
      OffsetDateTime expiryTime = OffsetDateTime.now().plusMinutes(10);
      BlobServiceSasSignatureValues values = new BlobServiceSasSignatureValues(expiryTime, permission);

      String sasToken = blobClient.generateSas(values);
      return String.format("%s?%s", blobClient.getBlobUrl(), sasToken);
    } catch (Exception e) {
      log.error("Failed to generate SAS URL for image {}", imageId, e);
      // Fallback: Generate AI service signed URL
      long expiryTs = (System.currentTimeMillis() / 1000L) + (3 * 3600);
      String token = tokenService.generateToken(eventId, imageId, expiryTs);
      return String.format("%s/images/%s/images/%s?token=%s",
          trimSlash(aiProperties.getPublicBaseUrl()),
          eventId,
          imageId,
          token);
    }
  }

  @SuppressWarnings("unchecked")
  private List<Map<String, Object>> safeList(Object obj) {
    if (obj instanceof List<?>) {
      return (List<Map<String, Object>>) obj;
    }
    return List.of();
  }

  // -------------------------
  // PAGINATION
  // -------------------------
  private SearchResponse paginate(MatchBuckets buckets, int page, int size) {

    List<ImageMatch> combined = new ArrayList<>();
    combined.addAll(buckets.strong);
    combined.addAll(buckets.weak);

    int total = combined.size();
    int from = (page - 1) * size;

    if (from >= total) {
      return new SearchResponse(total, page, size, false, List.of(), List.of());
    }

    int to = Math.min(from + size, total);

    List<ImageMatch> pageSlice = combined.subList(from, to);

    List<ImageMatch> strongPage = pageSlice.stream()
        .filter(buckets.strong::contains)
        .toList();

    List<ImageMatch> weakPage = pageSlice.stream()
        .filter(buckets.weak::contains)
        .toList();

    boolean hasMore = to < total;

    return new SearchResponse(total, page, size, hasMore, strongPage, weakPage);
  }
}
