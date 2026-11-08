# AI-Assisted Interview Exercise: Room Booking API

## Scenario

Your company has shared meeting rooms, but employees keep double-booking them.
Build a small HTTP API that lets employees reserve rooms, view reservations,
and cancel bookings.

This is an interview mockup, not a production service. Use AI to help implement
it, but be prepared to explain the design and demonstrate that it works.

**Timebox:** 60-75 minutes.

**Language and framework:** Your choice. Use familiar tools rather than spending
the exercise learning a new framework.

## What makes this exercise interesting

The main challenge is maintaining consistent state across requests:

- Two reservations for the same room must not overlap.
- Adjacent reservations are allowed.
- Cancelling a reservation makes that time available again.
- Invalid requests must not partially change the stored state.

There are no CSV files, batch reports, or overdue-item flags.

## Scope

Use an in-memory store with two predefined, case-sensitive room IDs:

- `cedar`
- `maple`

Data does not need to survive a restart. Authentication, databases, recurring
meetings, room capacity, and distributed concurrency are out of scope.

For the core exercise, assume requests are processed sequentially. Concurrency
is a follow-up discussion, not a hidden requirement.

## API Contract

### Create a booking

`POST /bookings`

```json
{
  "room_id": "cedar",
  "organizer": "Ada",
  "start": "2026-11-09T10:00:00Z",
  "end": "2026-11-09T11:00:00Z"
}
```

Return `201 Created` with the booking, including a server-generated unique `id`.
Clients must not choose or overwrite booking IDs.

### List bookings for a room

`GET /rooms/cedar/bookings`

Return `200 OK` with a JSON array of that room's active bookings, sorted by start
time. Return an empty array when the room has no bookings.

### Get one booking

`GET /bookings/{id}`

Return `200 OK` with the booking, or `404 Not Found` if it does not exist.

### Cancel a booking

`DELETE /bookings/{id}`

Return `204 No Content` when the booking is removed. Return `404 Not Found` if
the ID does not exist, including when the booking was already cancelled.

Cancelled bookings must not appear in list or get responses.

## Validation and Error Behavior

- All four create fields are required and must be strings.
- Reject unexpected create fields, including a client-supplied `id`.
- `organizer` must be nonempty after trimming; store the trimmed value.
- Room IDs must match one of the predefined rooms exactly.
- Accept timestamps only in the UTC format `YYYY-MM-DDTHH:MM:SSZ`. Validate
  actual calendar dates and times, not just their textual shape.
- The start must be strictly before the end.
- Do not impose a "must be in the future" rule. Examples and tests should work
  regardless of the machine's current date.
- Malformed JSON, missing fields, wrong types, invalid timestamps, and invalid
  intervals return `400 Bad Request`.
- An unknown room or booking returns `404 Not Found`.
- An overlapping reservation returns `409 Conflict`.
- Failed requests leave existing bookings unchanged.

For create requests, validate the payload first, then check room existence,
then check for conflicts. This determines which error to return when a request
has more than one problem.

Use a consistent JSON error shape, for example:

```json
{
  "error": {
    "code": "BOOKING_CONFLICT",
    "message": "The room is already booked during this interval."
  }
}
```

## Overlap Rule

Treat bookings as half-open intervals: `[start, end)`.

Two bookings overlap when:

```text
new_start < existing_end AND existing_start < new_end
```

Only compare bookings for the same room. Compare parsed timestamps rather than
unvalidated input strings.

## Classroom Walkthrough

Run these requests in order:

| Step | Request | Expected result |
| --- | --- | --- |
| 1 | Book cedar from 10:00 to 11:00 for Ada | 201; save its ID as A |
| 2 | Book cedar from 10:30 to 11:30 for Lin | 409; no new booking |
| 3 | Book maple from 10:30 to 11:30 for Lin | 201 |
| 4 | Book cedar from 11:00 to 12:00 for Sam | 201; adjacent is allowed |
| 5 | List cedar bookings | 200; two bookings, ordered by start |
| 6 | Cancel booking A | 204 |
| 7 | Get booking A | 404 |
| 8 | Book cedar from 10:30 to 11:00 for Lin | 201; cancelled time is available |
| 9 | Cancel booking A again | 404 |

Use November 9, 2026 and the timestamp format above for all walkthrough times.

## Required Tests

Cover at least:

1. Creating and retrieving a valid booking.
2. Partial overlap, identical intervals, and both directions of containment.
3. Adjacent bookings on either side of an existing booking.
4. Overlapping times in different rooms.
5. Cancellation freeing the time slot.
6. Unknown room IDs and unknown booking IDs.
7. Missing fields, wrong types, unexpected fields, and blank organizers.
8. Invalid calendar dates, non-UTC timestamps, and start equal to or after end.
9. Correct sorting when bookings are inserted out of order.
10. Rejected requests leaving the booking list unchanged.

## Suggested Class Structure

- **10 minutes:** Read the contract and outline the state model and test cases.
- **25 minutes:** Implement the API with AI assistance.
- **20 minutes:** Test the boundary cases and run the walkthrough.
- **10 minutes:** Explain the code and critique the AI's assumptions.
- **Optional 10 minutes:** Discuss one extension below.

## Deliverables

- A runnable API.
- Automated tests for the core behavior.
- Short instructions for starting the server and running tests.
- A demonstration of the walkthrough.
- An explanation of one AI-generated suggestion you rejected or corrected.

Keep the implementation small. Separate request handling from booking rules
enough that the overlap logic can be tested without starting a server.

## Interview Follow-Ups

Choose one rather than trying to implement everything:

### Concurrent requests

Two requests both check availability before either saves its booking. Both
succeed. Explain why this happens and how you would make check-and-create
atomic in a database-backed service.

### Safe retries

A client times out after a booking succeeds and retries the request. Design
an idempotency-key contract so retries do not create duplicate bookings.
What should happen if the same key is reused with a different payload?

### Rescheduling

Add an operation that moves a booking to a different time. If the new time
conflicts, the original reservation must remain intact.

### Local time

Users want to submit local timestamps. Explain what additional information
the API needs and how daylight-saving transitions create ambiguous or
nonexistent times.

## Evaluation Rubric

Prioritize correctness and reasoning over the amount of generated code:

- **Business logic:** Correct overlap boundaries and room isolation.
- **API behavior:** Predictable responses and useful validation errors.
- **State integrity:** No mutations on failure; cancellation works consistently.
- **Testing:** Meaningful boundary cases, not only happy-path assertions.
- **AI judgment:** The candidate can explain, verify, and challenge generated code.
