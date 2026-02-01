/**
 * Smart Glasses Mobile Gateway
 * Push notification service.
 */

import 'package:flutter/material.dart';

class NotificationService with ChangeListener {
  void showNotification(String title, String body) {
    // Would use flutter_local_notifications or similar
    print('Notification: $title - $body');
  }

  void showNavigationStep(String instruction, int distance) {
    print('Navigation: $instruction ($distance m)');
  }

  void showProactiveSuggestion(String message) {
    print('Suggestion: $message');
  }

  void vibrate({int duration = 100}) {
    // Would use vibration plugin
    print('Vibrate for $duration ms');
  }
}