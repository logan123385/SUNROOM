#pragma once
#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include <atomic>
#include <thread>

#include "MusicTheory.hpp"
#include "core/ClipInfo.hpp"
#include "core/TypeIds.hpp"
#include "project/ProjectManager.hpp"

namespace magda {
class AudioEngine;
namespace sunroom {
class SunroomStudio final : public juce::Component,
                            private juce::Timer,
                            private ProjectManagerListener {
  public:
    explicit SunroomStudio(AudioEngine* engine);
    ~SunroomStudio() override;
    void paint(juce::Graphics&) override;
    void resized() override;
    void mouseDown(const juce::MouseEvent&) override;
    bool keyPressed(const juce::KeyPress&) override;
    void mouseWheelMove(const juce::MouseEvent&, const juce::MouseWheelDetails&) override;
    std::function<void()> onOpenStudio, onSave, onExport, onNewProject, onOpenProject;
    std::function<void(TrackId, ClipId)> onEditClip;

  private:
    AudioEngine* engine_;
    Options options_;
    Options previewOptions_;
    Journey preview_;
    bool previewValid_ = false;
    int tab_ = 0;
    int anchor_ = 2;
    int previewLayer_ = 2;
    int sampleOffset_ = 0;
    TrackId previewTrack_ = INVALID_TRACK_ID;
    std::vector<int> sounding_;
    double noteOffTime_ = 0;
    juce::String status_ = "Choose a feeling. Build a journey. Make it yours.";
    juce::String pairText_ =
        "Click a note to hear it. Shift-click another to hear the relationship.";
    juce::TextButton newProject_{"New project"}, openProject_{"Open project"},
        create_{"Build my journey"}, play_{"Play"}, stop_{"Stop"}, variation_{"New variation"},
        save_{"Save project"}, export_{"Export audio"}, undo_{"Undo"}, studio_{"Full studio"},
        ask_{"Ask SUNROOM"}, cancelAI_{"Stop"}, addPhrase_{"Add melody to song"},
        clearPhrase_{"Clear melody"}, library_{"Open sound folder"},
        applyRecipe_{"Use these settings"}, saveKey_{"Save to Keychain"};
    std::array<juce::TextButton, 4> tabs_;
    std::array<juce::TextButton, 4> moodButtons_;
    std::array<juce::ToggleButton, 7> layerButtons_;
    juce::ComboBox root_, length_, aiBackend_;
    juce::Slider tempo_, motion_, space_, warmth_;
    juce::TextEditor prompt_, answer_, remoteUrl_, remoteModel_, apiKey_;
    juce::String coachHistory_;
    std::array<std::array<bool, 16>, 7> melody_{};
    juce::Rectangle<int> hero_, left_, centre_, right_, noteArea_, melodyArea_, journeyArea_;
    std::vector<std::pair<juce::Rectangle<int>, TrackId>> trackHitboxes_;
    std::vector<std::pair<juce::Rectangle<int>, juce::File>> sampleHitboxes_;
    juce::Array<juce::File> samples_;
    juce::var recipe_;
    std::unique_ptr<juce::LookAndFeel> skin_;
    std::atomic<bool> cancelled_{false};
    std::atomic<bool> busy_{false};
    std::thread aiThread_;
    uint64_t projectRevision_ = 0;
    void timerCallback() override;
    void stopNotes();
    void audition(int note, bool together);
    void setTab(int);
    void buildJourney();
    void applyControls();
    void askCoach();
    void addMelody();
    void paintCreate(juce::Graphics&);
    void paintGarden(juce::Graphics&);
    void paintSounds(juce::Graphics&);
    void paintCoach(juce::Graphics&);
    void projectOpened(const ProjectInfo&) override;
    void projectClosed() override;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SunroomStudio)
};
// Shared vector artwork. Drawn at native resolution, never a scaled screenshot.
void drawSun(juce::Graphics& g, juce::Rectangle<float> bounds, float opacity = 1.0f);
}  // namespace sunroom
}  // namespace magda
