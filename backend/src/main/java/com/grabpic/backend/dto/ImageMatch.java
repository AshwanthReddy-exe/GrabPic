package com.grabpic.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class ImageMatch {
  private String imageId;
  private double score;
  String url;

  public ImageMatch(String imageId, double score) {
    this.imageId = imageId;
    this.score = score;
  }
}
