#pragma once
#include "MusicTheory.hpp"
#include "core/ClipInfo.hpp"
#include "core/DeviceInfo.hpp"
#include "core/TrackInfo.hpp"
#include "core/UndoManager.hpp"
#include "project/ProjectInfo.hpp"

namespace magda {
class AudioEngine;
namespace sunroom {
DeviceInfo makeDevice(const juce::String& id, const juce::String& name, bool instrument,
                      const std::vector<std::pair<int, float>>& params = {});
class CreateJourneyCommand final : public UndoableCommand {
  public:
    CreateJourneyCommand(Options options, AudioEngine* engine);
    void execute() override;
    void undo() override;
    juce::String getDescription() const override {
        return "Create SUNROOM journey";
    }
    const std::vector<TrackId>& trackIds() const {
        return ids_;
    }

  private:
    Options options_;
    AudioEngine* engine_;
    ProjectInfo before_;
    ProjectInfo after_;
    std::vector<TrackId> ids_;
    std::vector<TrackInfo> tracks_;
    std::vector<ClipInfo> clips_;
    bool captured_ = false;
    void applyProject(const ProjectInfo& info);
};
// Appends a new instrument track through MAGDA's normal undo stack.
TrackId addInstrument(int layer, const Options& options);
juce::File soundLibrary();
}  // namespace sunroom
}  // namespace magda
