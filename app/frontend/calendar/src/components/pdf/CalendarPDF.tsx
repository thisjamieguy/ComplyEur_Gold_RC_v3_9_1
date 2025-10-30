import { addDays, format, parseISO } from "date-fns";
import { Document, Page, StyleSheet, Text, View } from "@react-pdf/renderer";

import type { TripRecord } from "../../hooks/useTrips";
import type { EmployeeRecord } from "../../hooks/useEmployees";

const styles = StyleSheet.create({
  page: {
    padding: 32,
    backgroundColor: "#ffffff",
    fontFamily: "Helvetica",
    color: "#1f2937",
    fontSize: 11,
  },
  heading: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 4,
  },
  subheading: {
    fontSize: 12,
    color: "#4b5563",
    marginBottom: 18,
  },
  section: {
    marginBottom: 18,
  },
  employeeTitle: {
    fontSize: 13,
    fontWeight: "bold",
    marginBottom: 8,
  },
  table: {
    display: "flex",
    flexDirection: "column",
    borderRadius: 6,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  tableHeader: {
    display: "flex",
    flexDirection: "row",
    backgroundColor: "#0f172a",
    color: "#ffffff",
  },
  headerCell: {
    flexGrow: 1,
    paddingVertical: 6,
    paddingHorizontal: 8,
    fontSize: 10,
    fontWeight: "bold",
  },
  row: {
    display: "flex",
    flexDirection: "row",
    alignItems: "stretch",
  },
  cell: {
    flexGrow: 1,
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
    fontSize: 10,
  },
  jobCell: {
    flexGrow: 1.2,
    flexDirection: "row",
    alignItems: "center",
  },
  jobLabel: {
    marginLeft: 6,
  },
  swatch: {
    width: 10,
    height: 10,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: "#ffffff",
  },
  purposeText: {
    marginTop: 2,
    fontSize: 9,
    color: "#64748b",
  },
  ghostBadge: {
    marginTop: 2,
    fontSize: 8,
    color: "#ef4444",
    fontStyle: "italic",
  },
});

interface CalendarPDFProps {
  employees: EmployeeRecord[];
  trips: TripRecord[];
  startDate: Date;
  weeks: number;
  jobColours: Record<string, string>;
}

const getTripColourKey = (trip: TripRecord) => trip.job_ref?.trim() || `country:${trip.country}`;

export function CalendarPDF({ employees, trips, startDate, weeks, jobColours }: CalendarPDFProps) {
  const endDate = addDays(startDate, weeks * 7 - 1);

  const tripsInRange = trips.filter((trip) => {
    const start = parseISO(trip.start_date);
    const end = parseISO(trip.end_date);
    return end >= startDate && start <= endDate;
  });

  const grouped = employees.map((employee) => ({
    employee,
    trips: tripsInRange
      .filter((trip) => trip.employee_id === employee.id)
      .sort((a, b) => a.start_date.localeCompare(b.start_date)),
  }));

  const totalTrips = tripsInRange.length;

  return (
    <Document title="Maavsi Calendar Export">
      <Page size="A4" style={styles.page} wrap>
        <View style={styles.section}>
          <Text style={styles.heading}>Maavsi Calendar Export</Text>
          <Text style={styles.subheading}>
            {format(startDate, "dd MMM yyyy")} → {format(endDate, "dd MMM yyyy")} ({weeks} week
            {weeks === 1 ? "" : "s"}) — {totalTrips} trip{totalTrips === 1 ? "" : "s"}
          </Text>
        </View>

        {grouped.every((group) => group.trips.length === 0) ? (
          <Text>No trips scheduled within this window.</Text>
        ) : (
          grouped
            .filter((group) => group.trips.length > 0)
            .map(({ employee, trips: employeeTrips }) => (
              <View key={employee.id} style={styles.section} wrap={false}>
                <Text style={styles.employeeTitle}>{employee.name}</Text>
                <View style={styles.table}>
                  <View style={styles.tableHeader}>
                    <Text style={{ ...styles.headerCell, flexGrow: 1.2 }}>Job Reference</Text>
                    <Text style={styles.headerCell}>Country</Text>
                    <Text style={styles.headerCell}>Dates</Text>
                    <Text style={styles.headerCell}>Status</Text>
                  </View>
                  {employeeTrips.map((trip) => {
                    const colourKey = getTripColourKey(trip);
                    const badgeColour = jobColours[colourKey] ?? "#2563eb";
                    const start = format(parseISO(trip.start_date), "dd MMM yyyy");
                    const end = format(parseISO(trip.end_date), "dd MMM yyyy");
                    return (
                      <View key={trip.id} style={styles.row} wrap={false}>
                        <View style={{ ...styles.cell, ...styles.jobCell }}>
                          <View style={{ ...styles.swatch, backgroundColor: badgeColour }} />
                          <Text style={styles.jobLabel}>
                            {trip.job_ref?.trim() ? trip.job_ref : "No job reference"}
                          </Text>
                        </View>
                        <Text style={styles.cell}>{trip.country}</Text>
                        <Text style={styles.cell}>
                          {start} → {end}
                        </Text>
                        <View style={styles.cell}>
                          <Text>{trip.ghosted ? "Ghosted" : "Active"}</Text>
                          {trip.purpose && <Text style={styles.purposeText}>{trip.purpose}</Text>}
                          {trip.ghosted && <Text style={styles.ghostBadge}>Hidden from live view</Text>}
                        </View>
                      </View>
                    );
                  })}
                </View>
              </View>
            ))
        )}
      </Page>
    </Document>
  );
}


