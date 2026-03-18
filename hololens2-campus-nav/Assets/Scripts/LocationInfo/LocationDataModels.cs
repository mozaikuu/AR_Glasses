using System;
using UnityEngine;

namespace LocationInfoSystem
{
    /// <summary>
    /// Types of places in the navigation system.
    /// </summary>
    public enum PlaceType
    {
        General = 0,
        Office = 1,
        LectureRoom = 2,
        Lab = 3,
        Cafeteria = 4,
        Library = 5,
        EmergencyExit = 6
    }

    /// <summary>
    /// Represents a staff member (TA, professor, etc.)
    /// </summary>
    [Serializable]
    public class StaffMember
    {
        public string name;
        public string role;
        public string email;
        public string[] officeDays;
        public string officeHours;
    }

    /// <summary>
    /// Represents a scheduled lecture.
    /// </summary>
    [Serializable]
    public class Lecture
    {
        public string courseName;
        public string courseCode;
        public string instructor;
        public string day;
        public string startTime;
        public string endTime;
    }

    /// <summary>
    /// Serializable class matching the navigation.json structure.
    /// </summary>
    [Serializable]
    public class LocationData
    {
        public string id;
        public string name;
        public int floor;
        public Vector2 coordinates; // x, y from JSON
        public string description;
        public string additional_info;
        public PlaceType placeType;
        public float proximityRadius = 2.0f;

        // Type-specific data
        public StaffMember[] staff;      // For offices
        public Lecture[] lectures;       // For lecture rooms

        /// <summary>
        /// Get display-friendly place type name.
        /// </summary>
        public string GetPlaceTypeDisplayName()
        {
            switch (placeType)
            {
                case PlaceType.Office:
                    return "Office";
                case PlaceType.LectureRoom:
                    return "Lecture Room";
                case PlaceType.Lab:
                    return "Laboratory";
                case PlaceType.Cafeteria:
                    return "Cafeteria";
                case PlaceType.Library:
                    return "Library";
                case PlaceType.EmergencyExit:
                    return "Emergency Exit";
                default:
                    return "Location";
            }
        }

        /// <summary>
        /// Check if this location has staff information.
        /// </summary>
        public bool HasStaffInfo()
        {
            return staff != null && staff.Length > 0;
        }

        /// <summary>
        /// Check if this location has lecture schedule information.
        /// </summary>
        public bool HasLectureInfo()
        {
            return lectures != null && lectures.Length > 0;
        }

        /// <summary>
        /// Get lectures for a specific day.
        /// </summary>
        public Lecture[] GetLecturesForDay(string day)
        {
            if (lectures == null || lectures.Length == 0)
                return new Lecture[0];

            var result = new System.Collections.Generic.List<Lecture>();
            foreach (var lecture in lectures)
            {
                if (lecture.day.Equals(day, StringComparison.OrdinalIgnoreCase))
                {
                    result.Add(lecture);
                }
            }
            return result.ToArray();
        }

        /// <summary>
        /// Get today's lectures based on system date.
        /// </summary>
        public Lecture[] GetTodaysLectures()
        {
            string today = DateTime.Now.DayOfWeek.ToString();
            return GetLecturesForDay(today);
        }
    }

    /// <summary>
    /// Wrapper for the navigation.json root structure.
    /// </summary>
    [Serializable]
    public class NavigationDataRoot
    {
        public BuildingInfo building;
        public LocationData[] locations;
    }

    /// <summary>
    /// Building information from navigation.json.
    /// </summary>
    [Serializable]
    public class BuildingInfo
    {
        public string name;
        public string address;
    }
}
