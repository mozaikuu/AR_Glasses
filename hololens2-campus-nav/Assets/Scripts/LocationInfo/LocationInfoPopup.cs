using System.Collections.Generic;
using System.Text;
using TMPro;
using UnityEngine;

namespace LocationInfoSystem
{
    /// <summary>
    /// Displays location information in a world-space popup.
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

        [Header("Behavior")]
        [SerializeField] private bool billboardMode = true;
        [SerializeField] private bool followUser = false;
        [SerializeField] private float followDistance = 2.0f;
        [SerializeField] private float hideAfterSeconds = 0f;

        [Header("Animation")]
        [SerializeField] private string showTrigger = "Show";
        [SerializeField] private string hideTrigger = "Hide";
        [SerializeField] private float destroyAfterHide = 1.0f;

        private LocationData currentLocation;
        private Transform cameraTransform;
        private bool isVisible;
        private float showTime;

        public System.Action OnShow;
        public System.Action OnHide;

        private void Awake()
        {
            if (Camera.main != null)
            {
                cameraTransform = Camera.main.transform;
            }

            if (popupCanvas != null)
            {
                popupCanvas.enabled = false;
            }

            ClearContainers();
        }

        private void Update()
        {
            if (!isVisible)
            {
                return;
            }

            if (cameraTransform == null && Camera.main != null)
            {
                cameraTransform = Camera.main.transform;
            }

            if (billboardMode && cameraTransform != null)
            {
                transform.rotation = Quaternion.LookRotation(transform.position - cameraTransform.position, Vector3.up);
            }

            if (followUser && cameraTransform != null)
            {
                Vector3 targetPosition = cameraTransform.position + cameraTransform.forward * followDistance;
                transform.position = Vector3.Lerp(transform.position, targetPosition, Time.deltaTime * 5f);
            }

            if (hideAfterSeconds > 0f && Time.time - showTime >= hideAfterSeconds)
            {
                Hide();
            }
        }

        public void Show(LocationData data)
        {
            if (data == null)
            {
                Debug.LogWarning("[LocationInfoPopup] Cannot show null location data.");
                return;
            }

            currentLocation = data;
            showTime = Time.time;
            isVisible = true;

            if (followUser && cameraTransform != null)
            {
                transform.position = cameraTransform.position + cameraTransform.forward * followDistance;
            }

            if (popupCanvas != null)
            {
                popupCanvas.enabled = true;
            }

            PopulateUi();

            if (animator != null && !string.IsNullOrWhiteSpace(showTrigger))
            {
                animator.SetTrigger(showTrigger);
            }

            OnShow?.Invoke();
        }

        public void Hide()
        {
            if (!isVisible)
            {
                return;
            }

            isVisible = false;

            if (animator != null && !string.IsNullOrWhiteSpace(hideTrigger))
            {
                animator.SetTrigger(hideTrigger);
            }

            OnHide?.Invoke();

            if (destroyAfterHide > 0f)
            {
                Destroy(gameObject, destroyAfterHide);
            }
            else if (popupCanvas != null)
            {
                popupCanvas.enabled = false;
            }
        }

        private void PopulateUi()
        {
            if (titleText != null)
            {
                titleText.text = currentLocation.name;
            }

            if (subtitleText != null)
            {
                string floorText = currentLocation.floor >= 0 ? $"Floor {currentLocation.floor}" : string.Empty;
                string typeText = currentLocation.GetPlaceTypeDisplayName();
                subtitleText.text = string.IsNullOrEmpty(floorText) ? typeText : $"{typeText} - {floorText}";
            }

            ClearContainers();

            if (currentLocation.HasStaffInfo())
            {
                PopulateStaffInfo();
                return;
            }

            if (currentLocation.HasLectureInfo())
            {
                PopulateLectureInfo();
                return;
            }

            PopulateGenericInfo();
        }

        private void PopulateStaffInfo()
        {
            if (contentText != null)
            {
                contentText.text = "Office staff";
            }

            if (staffContainer == null || staffCardPrefab == null)
            {
                PopulateStaffTextFallback();
                return;
            }

            foreach (StaffMember staff in currentLocation.staff)
            {
                GameObject card = Instantiate(staffCardPrefab, staffContainer);

                SetCardText(card, "Name", staff.name);
                SetCardText(card, "Desk", string.IsNullOrWhiteSpace(staff.deskLabel) ? "Desk not listed" : $"Desk: {staff.deskLabel}");
                SetCardText(card, "Role", staff.role);
                SetCardText(card, "Email", string.IsNullOrWhiteSpace(staff.email) ? string.Empty : $"Email: {staff.email}");
                SetCardText(card, "Hours", BuildStaffAvailabilityText(staff));
                SetCardText(card, "Courses", BuildCoursesText(staff));
            }
        }

        private void PopulateStaffTextFallback()
        {
            if (contentText == null)
            {
                return;
            }

            StringBuilder builder = new StringBuilder();
            builder.AppendLine("Office staff");
            builder.AppendLine();

            foreach (StaffMember staff in currentLocation.staff)
            {
                builder.AppendLine($"<b>{staff.name}</b>");
                if (!string.IsNullOrWhiteSpace(staff.deskLabel))
                {
                    builder.AppendLine($"Desk: {staff.deskLabel}");
                }

                if (!string.IsNullOrWhiteSpace(staff.role))
                {
                    builder.AppendLine(staff.role);
                }

                if (!string.IsNullOrWhiteSpace(staff.email))
                {
                    builder.AppendLine($"Email: {staff.email}");
                }

                builder.AppendLine(BuildStaffAvailabilityText(staff));

                string coursesText = BuildCoursesText(staff);
                if (!string.IsNullOrWhiteSpace(coursesText))
                {
                    builder.AppendLine(coursesText);
                }

                builder.AppendLine();
            }

            contentText.text = builder.ToString().TrimEnd();
        }

        private void PopulateLectureInfo()
        {
            Lecture[] todaysLectures = currentLocation.GetTodaysLectures();

            if (contentText != null)
            {
                contentText.text = todaysLectures.Length > 0 ? "Today's schedule" : "No lectures scheduled today";
            }

            if (lecturesContainer == null || lectureCardPrefab == null)
            {
                PopulateLectureTextFallback(todaysLectures);
                return;
            }

            if (todaysLectures.Length > 0)
            {
                foreach (Lecture lecture in todaysLectures)
                {
                    CreateLectureCard(lecture.courseName, lecture.courseCode, lecture.instructor, $"{lecture.startTime} - {lecture.endTime}");
                }

                return;
            }

            Dictionary<string, List<Lecture>> lecturesByDay = GroupLecturesByDay();
            foreach (KeyValuePair<string, List<Lecture>> dayEntry in lecturesByDay)
            {
                CreateLectureCard(dayEntry.Key, string.Empty, string.Empty, $"{dayEntry.Value.Count} lecture(s)");
            }
        }

        private void PopulateLectureTextFallback(Lecture[] todaysLectures)
        {
            if (contentText == null)
            {
                return;
            }

            StringBuilder builder = new StringBuilder();
            if (todaysLectures.Length > 0)
            {
                builder.AppendLine("Today's schedule");
                builder.AppendLine();

                foreach (Lecture lecture in todaysLectures)
                {
                    builder.AppendLine($"<b>{lecture.courseName}</b>");
                    builder.AppendLine($"{lecture.courseCode} - {lecture.instructor}");
                    builder.AppendLine($"{lecture.startTime} - {lecture.endTime}");
                    builder.AppendLine();
                }
            }
            else
            {
                builder.AppendLine("No lectures scheduled today");
                builder.AppendLine();
                builder.AppendLine("Weekly schedule");
                builder.AppendLine();

                foreach (KeyValuePair<string, List<Lecture>> dayEntry in GroupLecturesByDay())
                {
                    builder.AppendLine($"<b>{dayEntry.Key}</b>");
                    foreach (Lecture lecture in dayEntry.Value)
                    {
                        builder.AppendLine($"{lecture.startTime} - {lecture.endTime}: {lecture.courseName} ({lecture.instructor})");
                    }

                    builder.AppendLine();
                }
            }

            contentText.text = builder.ToString().TrimEnd();
        }

        private Dictionary<string, List<Lecture>> GroupLecturesByDay()
        {
            Dictionary<string, List<Lecture>> lecturesByDay = new Dictionary<string, List<Lecture>>();

            foreach (Lecture lecture in currentLocation.lectures)
            {
                if (!lecturesByDay.ContainsKey(lecture.day))
                {
                    lecturesByDay[lecture.day] = new List<Lecture>();
                }

                lecturesByDay[lecture.day].Add(lecture);
            }

            return lecturesByDay;
        }

        private void CreateLectureCard(string courseName, string courseCode, string instructor, string timeText)
        {
            GameObject card = Instantiate(lectureCardPrefab, lecturesContainer);
            SetCardText(card, "CourseName", courseName);
            SetCardText(card, "CourseCode", courseCode);
            SetCardText(card, "Instructor", instructor);
            SetCardText(card, "Time", timeText);
        }

        private void PopulateGenericInfo()
        {
            if (contentText == null)
            {
                return;
            }

            StringBuilder builder = new StringBuilder();

            if (!string.IsNullOrWhiteSpace(currentLocation.description))
            {
                builder.AppendLine(currentLocation.description);
            }

            if (!string.IsNullOrWhiteSpace(currentLocation.additional_info))
            {
                if (builder.Length > 0)
                {
                    builder.AppendLine();
                }

                builder.AppendLine(currentLocation.additional_info);
            }

            contentText.text = builder.ToString().TrimEnd();
        }

        private string BuildStaffAvailabilityText(StaffMember staff)
        {
            List<string> lines = new List<string>();

            if (staff.officeDays != null && staff.officeDays.Length > 0)
            {
                lines.Add($"Days: {string.Join(", ", staff.officeDays)}");
            }

            if (!string.IsNullOrWhiteSpace(staff.officeHours))
            {
                lines.Add($"Hours: {staff.officeHours}");
            }

            lines.Add(staff.IsAvailableToday() ? "Status: Available today" : "Status: Not scheduled today");
            return string.Join("\n", lines);
        }

        private string BuildCoursesText(StaffMember staff)
        {
            if (staff.coursesTaught == null || staff.coursesTaught.Length == 0)
            {
                return string.Empty;
            }

            return $"Teaches: {string.Join(", ", staff.coursesTaught)}";
        }

        private void SetCardText(GameObject card, string childName, string value)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                return;
            }

            TextMeshProUGUI targetText = card.transform.Find(childName)?.GetComponent<TextMeshProUGUI>();
            if (targetText != null)
            {
                targetText.text = value;
            }
        }

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

        public bool IsVisible => isVisible;

        public LocationData GetCurrentLocation()
        {
            return currentLocation;
        }

        public void SetFollowUser(bool follow, float distance = 2.0f)
        {
            followUser = follow;
            followDistance = distance;
        }

        public void SetBillboardMode(bool billboard)
        {
            billboardMode = billboard;
        }
    }
}
