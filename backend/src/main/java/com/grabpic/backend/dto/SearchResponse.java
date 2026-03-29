package com.grabpic.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class SearchResponse {
  private int total;
  private int page;
  private int size;
  private boolean hasMore;

  private List<ImageMatch> strongMatches;
  private List<ImageMatch> weakMatches;
}
