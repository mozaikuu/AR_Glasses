using System.Collections.Generic;
using System.Text;
using UnityEngine;
using TMPro;
using LocationInfoSystem;

namespace LocationInfoSystem
{
    /// <summary>
    /// Displays location information in a popup UI.
    /// Designed to work with MRTK for HoloLens.
    /// </summary>
    public class LocationInfoPopup : MonoBehaviour
    {
        [Header("UI Components")]
        [SerializeField] private TextMeshProUGUI titleText;
        [SerializeField] private TextMeshProUGUI subtitleText;
        [SerializeField] private TextMeshProUGUI contentText;
        [SerializeField] private Transform staffContainer;
        [SerializeField] private Transform lecturesContainer;
        [SerializeField] private GameObject staffCardPrefab;
        [SerializeField] private GameObject lectureCardPrefab;

        [Header("Visual")]
        [SerializeField] private Canvas popupCanvas;
        [SerializeField] private Animator animator;
        [SerializeField] private GameObject backplate;

        [Header("Behavior")]
        [SerializeField] private bool billboardMode = true;
        [SerializeField] private bool followUser = false;
        [SerializeField] private float followDistance = 2.0f;
        [SerializeField] private float hideAfterSeconds = 0f; // 0 = don't auto-hide

        [Header("Animation")]
        [SerializeField] private string showTrigger = "Show";
        [SerializeField] private string hideTrigger = "Hide";
        [SerializeField] private float destroyAfterHide = 1.0f;

        // Runtime
        private LocationData currentLocation;
        private Transform cameraTransform;
        private bool isVisible = false;
        private float showTime;

        // Events
        public System.Action OnShow;
        public System.Action OnHide;

        private void Awake()
        {
            // Find camera
            if (Camera.main != null)
            {
                cameraTransform = Camera.main.transform;
            }

            // Hide initially
            if (popupCanvas != null)
            {
                popupCanvas.enabled = false;
            }

            // Clear containers
            ClearContainers();
        }

        private void Update()
        {
            if (!isVisible)
                return;

            // Billboard mode - always face camera
            if (billboardMode && cameraTransform != null)
            {
                transform.rotation = Quaternion.LookRotation(
                    transform.position - cameraTransform.position,
                    Vector3.up
                );
            }

            // Follow user mode
            if (followUser && cameraTransform != null)
            {
                Vector3 targetPos = cameraTransform.position + cameraTransform.forward * followDistance;
                transform.position = Vector3.Lerp(transform.position, targetPos, Time.deltaTime * 5f);
            }

            // Auto-hide
            if (hideAfterSeconds > 0 && Time.time - showTime >= hideAfterSeconds)
            {
                Hide();
            }
        }

        /// <summary>
        /// Show the popup with location data.
        /// </summary>
        public void Show(LocationData data)
        {
            if (data == null)
            {
                Debug.LogWarning("[LocationInfoPopup] Cannot show null location data");
                return;
            }

            currentLocation = data;
            showTime = Time.time;
            isVisible = true;

            // Enable canvas
            if (popupCanvas != null)
            {
                popupCanvas.enabled = true;
            }

            // Populate UI
            PopulateUI();

            // Trigger animation
            if (animator != null)
            {
                animator.SetTrigger(showTrigger);
            }

            OnShow?.Invoke();

            Debug.Log($"[LocationInfoPopup] Showing: {data.name}");
        }

        /// <summary>
        /// Hide the popup.
        /// </summary>
        public void Hide()
        {
            if (!isVisible)
                return;

            isVisible = false;

            // Trigger animation
            if (animator != null)
            {
                animator.SetTrigger(hideTrigger);
            }

            OnHide?.Invoke();

            // Destroy after animation
            if (destroyAfterHide > 0)
            {
                Destroy(gameObject, destroyAfterHide);
            }
            else
            {
                // Just disable canvas
                if (popupCanvas != null)
                {
                    popupCanvas.enabled = false;
                }
            }
        }

        /// <summary>
        /// Populate the UI with location data.
        /// </summary>
        private void PopulateUI()
        {
            // Title
            if (titleText != null)
            {
                titleText.text = currentLocation.name;
            }

            // Subtitle (type + floor)
            if (subtitleText != null)
            {
                string floorText = currentLocation.floor >= 0 ? $"Floor {currentLocation.floor}" : "";
                string typeText = currentLocation.GetPlaceTypeDisplayName();
                subtitleText.text = $"{typeText} • {floorText}";
            }

            // Clear previous content
            ClearContainers();

            // Populate based on location type
            if (currentLocation.HasStaffInfo())
            {
                PopulateStaffInfo();
            }
            else if (currentLocation.HasLectureInfo())
            {
                PopulateLectureInfo();
            }
            else
            {
                // Generic location
                PopulateGenericInfo();
            }
        }

        /// <summary>
        /// Populate staff information for offices.
        /// </summary>
        private void PopulateStaffInfo()
        {
            if (contentText != null)
            {
                contentText.text = "Staff:";
            }

            if (staffContainer == null || staffCardPrefab == null)
            {
                // Fallback to text
                if (contentText != null)
                {
                    StringBuilder sb = new StringBuilder();
                    sb.AppendLine("Staff:");
                    sb.AppendLine();

                    foreach (var staff in currentLocation.staff)
                    {
                        sb.AppendLine($"<b>{staff.name}</b>");
                        sb.AppendLine($"{staff.role}");
                        sb.AppendLine($"📧 {staff.email}");
                        sb.AppendLine($"📅 {string.Join(", ", staff.officeDays)}");
                        sb.AppendLine($"🕐 {staff.officeHours}");
                        sb.AppendLine();
                    }

                    contentText.text = sb.ToString();
                }
                return;
            }

            // Instantiate staff cards
            foreach (var staff in currentLocation.staff)
            {
                GameObject card = Instantiate(staffCardPrefab, staffContainer);

                // Find text components in card
                var nameText = card.transform.Find("Name")?.GetComponent<TextMeshProUGUI>();
                var roleText = card.transform.Find("Role")?.GetComponent<TextMeshProUGUI>();
                var emailText = card.transform.Find("Email")?.GetComponent<TextMeshProUGUI>();
                var hoursText = card.transform.Find("Hours")?.GetComponent<TextMeshProUGUI>();

                if (nameText != null) nameText.text = staff.name;
                if (roleText != null) roleText.text = staff.role;
                if (emailText != null) emailText.text = staff.email;
                if (hoursText != null)
                {
                    hoursText.text = $"📅 {string.Join(", ", staff.officeDays)}\n🕐 {staff.officeHours}";
                }
            }
        }

        /// <summary>
        /// Populate lecture schedule for lecture halls.
        /// </summary>
        private void PopulateLectureInfo()
        {
            // Get today's lectures
            var todaysLectures = currentLocation.GetTodaysLectures();

            if (contentText != null)
            {
                if (todaysLectures.Length > 0)
                {
                    contentText.text = "Today's Lectures:";
                }
                else
                {
                    contentText.text = "No lectures scheduled today";
                }
            }

            if (lecturesContainer == null || lectureCardPrefab == null)
            {
                // Fallback to text
                if (contentText != null && todaysLectures.Length > 0)
                {
                    StringBuilder sb = new StringBuilder();
                    sb.AppendLine("Today's Lectures:");
                    sb.AppendLine();

                    foreach (var lecture in todaysLectures)
                    {
                        sb.AppendLine($"<b>{lecture.courseName}</b>");
                        sb.AppendLine($"{lecture.courseCode} - {lecture.instructor}");
                        sb.AppendLine($"🕐 {lecture.startTime} - {lecture.endTime}");
                        sb.AppendLine();
                    }

                    contentText.text = sb.ToString();
                }
                return;
            }

            // Instantiate lecture cards
            foreach (var lecture in todaysLectures)
            {
                GameObject card = Instantiate(lectureCardPrefab, lecturesContainer);

                var courseText = card.transform.Find("CourseName")?.GetComponent<TextMeshProUGUI>();
                var codeText = card.transform.Find("CourseCode")?.GetComponent<TextMeshProUGUI>();
                var instructorText = card.transform.Find("Instructor")?.GetComponent<TextMeshProUGUI>();
                var timeText = card.transform.Find("Time")?.GetComponent<TextMeshProUGUI>();

                if (courseText != null) courseText.text = lecture.courseName;
                if (codeText != null) codeText.text = lecture.courseCode;
                if (instructorText != null) instructorText.text = lecture.instructor;
                if (timeText != null) timeText.text = $"🕐 {lecture.startTime} - {lecture.endTime}";
            }

            // Show weekly schedule if no lectures today
            if (todaysLectures.Length == 0 && currentLocation.lectures.Length > 0)
            {
                if (contentText != null)
                {
                    contentText.text += "\n\nWeekly Schedule:";
                }

                // Group by day
                var lecturesByDay = new Dictionary<string, List<Lecture>>();
                foreach (var lecture in currentLocation.lectures)
                {
                    if (!lecturesByDay.ContainsKey(lecture.day))
                        lecturesByDay[lecture.day] = new List<Lecture>();
                    lecturesByDay[lecture.day].Add(lecture);
                }

                foreach (var day in lecturesByDay.Keys)
                {
                    GameObject card = Instantiate(lectureCardPrefab, lecturesContainer);
                    var courseText = card.transform.Find("CourseName")?.GetComponent<TextMeshProUGUI>();
                    if (courseText != null) courseText.text = day;

                    var timeText = card.transform.Find("Time")?.GetComponent<TextMeshProUGUI>();
                    if (timeText != null)
                    {
                        var lectures = lecturesByDay[day];
                        timeText.text = $"{lectures.Count} lecture(s)";
                    }
                }
            }
        }

        /// <summary>
        /// Populate generic location info.
        /// </summary>
        private void PopulateGenericInfo()
        {
            if (contentText != null)
            {
                StringBuilder sb = new StringBuilder();

                if (!string.IsNullOrEmpty(currentLocation.description))
                {
                    sb.AppendLine(currentLocation.description);
                    sb.AppendLine();
                }

                if (!string.IsNullOrEmpty(currentLocation.additional_info))
                {
                    sb.AppendLine(currentLocation.additional_info);
                }

                contentText.text = sb.ToString();
            }
        }

        /// <summary>
        /// Clear all dynamic content containers.
        /// </summary>
        private void ClearContainers()
        {
            if (staffContainer != null)
            {
                foreach (Transform child in staffContainer)
                {
                    Destroy(child.gameObject);
                }
            }

            if (lecturesContainer != null)
            {
                foreach (Transform child in lecturesContainer)
                {
                    Destroy(child.gameObject);
                }
            }
        }

        /// <summary>
        /// Check if popup is currently visible.
        /// </summary>
        public bool IsVisible => isVisible;

        /// <summary>
        /// Get the current location data.
        /// </summary>
        public LocationData GetCurrentLocation()
        {
            return currentLocation;
        }

        /// <summary>
        /// Set the popup to follow the user.
        /// </summary>
        public void SetFollowUser(bool follow, float distance = 2.0f)
        {
            followUser = follow;
            followDistance = distance;
        }

        /// <summary>
        /// Set billboard mode.
        /// </summary>
        public void SetBillboardMode(bool billboard)
        {
            billboardMode = billboard;
        }
    }
}
