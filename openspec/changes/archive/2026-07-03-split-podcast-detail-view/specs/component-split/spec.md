# Podcast Component Split Specs

## ADDED Requirements

### Requirement: Single Responsibility Principle in Detail View
The `PodcastDetailView` component MUST delegate specific domain logic to isolated subcomponents and act strictly as a layout orchestrator.

#### Scenario: Audio control isolation
- Given the user wants to interact with the audio player
- When they adjust the volume or scrub the timeline
- Then the logic must reside within `AudioPlayerControl.jsx` and not clutter the root detail view component.

#### Scenario: Subcomponent encapsulation
- Given a developer views the `frontend/src/components/podcast/` directory
- When they inspect the file structure
- Then they must find discrete files mapping directly to functional regions of the detail view (Player, Chat, Transcripts, Modals).
