#include "SunroomActions.hpp"

#include "core/AppPaths.hpp"
#include "core/ClipManager.hpp"
#include "core/TrackCommands.hpp"
#include "core/TrackManager.hpp"
#include "engine/AudioEngine.hpp"
#include "project/ProjectManager.hpp"
#include "ui/state/TimelineController.hpp"

namespace magda::sunroom {
DeviceInfo makeDevice(const juce::String& id, const juce::String& name, bool instrument,
                      const std::vector<std::pair<int, float>>& params) {
    DeviceInfo d;
    d.pluginId = id;
    d.uniqueId = id;
    d.fileOrIdentifier = id;
    d.name = name;
    d.manufacturer = "MAGDA / SUNROOM";
    d.format = PluginFormat::Internal;
    d.isInstrument = instrument;
    d.deviceType = instrument ? DeviceType::Instrument : DeviceType::Effect;
    d.canReceiveMidi = instrument;
    // Presets use the same real/display values as the device controls. The
    // processor converts them to its native parameter range during creation.
    // A DeviceState document instead stores native values (often normalized
    // 0..1); putting dB or milliseconds in that document silently mutes voices.
    for (auto [index, value] : params) {
        ParameterInfo parameter;
        parameter.paramIndex = index;
        parameter.currentValue = value;
        d.parameters.push_back(std::move(parameter));
    }
    return d;
}
namespace {
void installSound(TrackId id, int layer, const Options& o) {
    auto& tm = TrackManager::getInstance();
    const auto& l = layers[static_cast<size_t>(layer)];
    std::vector<std::pair<int, float>> p;
    if (layer == 0)
        p = {{0, 3},     {1, -8},    {4, 1},
             {5, -18},   {7, 7},     {17, 650 + (1 - o.warmth) * 2200},
             {18, .15f}, {24, 1400}, {25, 1200},
             {26, .75f}, {27, 3600}, {43, -8}};
    if (layer == 1)
        p = {{0, 0},   {1, -3},   {4, 3},    {5, -24},  {17, 280}, {18, .1f},
             {24, 15}, {25, 300}, {26, .7f}, {27, 180}, {43, -7}};
    tm.addDeviceToTrack(id, makeDevice(l.plugin, l.name, true, p));
    if (layer == 2 || layer == 6 || layer == 3) {
        tm.addDeviceToTrack(id, makeDevice("magda_delay", "Orbit / echoes", false,
                                           {{0, static_cast<float>(45000 / o.tempo)},
                                            {3, .26f + o.space * .18f},
                                            {4, layer == 3 ? .14f : .23f},
                                            {5, -.3f},
                                            {6, .7f}}));
    }
    if (layer == 0 || layer == 2 || layer == 6) {
        tm.addDeviceToTrack(id, makeDevice("magda_reverb", "Horizon / space", false,
                                           {{0, 1},
                                            {1, .20f + o.space * .24f},
                                            {2, 35},
                                            {3, 40 + o.space * 35},
                                            {4, 50},
                                            {5, 180},
                                            {6, 5500},
                                            {7, 120},
                                            {8, -2}}));
    }
    tm.setTrackColour(id, juce::Colour(l.colour));
    tm.setTrackVolume(id, l.volume);
}
class AddInstrumentCommand final : public UndoableCommand {
  public:
    AddInstrumentCommand(int layer, Options options) : layer_(layer), options_(options) {}
    void execute() override {
        auto& tm = TrackManager::getInstance();
        if (captured_) {
            tm.restoreTrack(track_);
            return;
        }
        auto id = tm.createTrack(layers[static_cast<size_t>(layer_)].name, TrackType::Audio);
        installSound(id, layer_, options_);
        track_ = *tm.getTrack(id);
        captured_ = true;
    }
    void undo() override {
        TrackManager::getInstance().deleteTrack(track_.id);
    }
    juce::String getDescription() const override {
        return "Add " + track_.name;
    }
    TrackId id() const {
        return track_.id;
    }

  private:
    int layer_;
    Options options_;
    TrackInfo track_;
    bool captured_ = false;
};
}  // namespace
TrackId addInstrument(int layer, const Options& options) {
    layer = juce::jlimit(0, 6, layer);
    auto command = std::make_unique<AddInstrumentCommand>(layer, sanitise(options));
    auto* raw = command.get();
    UndoManager::getInstance().executeCommand(std::move(command));
    return raw->id();
}
CreateJourneyCommand::CreateJourneyCommand(Options options, AudioEngine* engine)
    : options_(sanitise(options)), engine_(engine) {}

void CreateJourneyCommand::applyProject(const ProjectInfo& info) {
    auto& pm = ProjectManager::getInstance();
    // Only the fields owned by this command. Preserve path/name and UI state
    // when undoing after a save or after the user changes their view.
    auto& live = pm.getMutableProjectInfo();
    live.keyRoot = info.keyRoot;
    live.keyQuality = info.keyQuality;
    live.sunroomMood = info.sunroomMood;
    live.sunroomGuide = info.sunroomGuide;
    live.markers = info.markers;
    pm.setTempo(info.tempo);
    pm.setTimeSignature(info.timeSignatureNumerator, info.timeSignatureDenominator);
    pm.setLoopSettings(info.loopEnabled, info.loopStartBeats, info.loopEndBeats);
    if (auto* timeline = TimelineController::getCurrent()) {
        timeline->dispatch(SetTempoEvent{info.tempo});
        timeline->dispatch(
            SetTimeSignatureEvent{info.timeSignatureNumerator, info.timeSignatureDenominator});
        if (info.loopEndBeats > info.loopStartBeats)
            timeline->dispatch(SetLoopRegionBeatsEvent{info.loopStartBeats, info.loopEndBeats});
        else
            timeline->dispatch(ClearLoopRegionEvent{});
        timeline->dispatch(SetLoopEnabledEvent{info.loopEnabled});
        std::vector<TimelineMarker> markers;
        for (const auto& marker : info.markers)
            markers.emplace_back(marker.id, marker.positionBeats, marker.name,
                                 juce::Colour(marker.colourArgb));
        timeline->dispatch(SetMarkersEvent{std::move(markers)});
    }
    if (engine_) {
        engine_->setTempo(info.tempo);
        engine_->setTimeSignature(info.timeSignatureNumerator, info.timeSignatureDenominator);
        engine_->setLoopRegionBeats(
            BeatRange{BeatPosition{info.loopStartBeats}, BeatPosition{info.loopEndBeats}});
        engine_->setLooping(info.loopEnabled);
    }
}
void CreateJourneyCommand::execute() {
    auto& tm = TrackManager::getInstance();
    auto& cm = ClipManager::getInstance();
    if (engine_)
        engine_->stop();
    ClipManager::BatchScope batch;
    if (captured_) {
        applyProject(after_);
        for (const auto& track : tracks_)
            tm.restoreTrack(track);
        for (const auto& clip : clips_)
            cm.restoreClip(clip);
        return;
    }
    before_ = ProjectManager::getInstance().getCurrentProjectInfo();
    after_ = before_;
    after_.tempo = options_.tempo;
    after_.timeSignatureNumerator = 4;
    after_.timeSignatureDenominator = 4;
    after_.keyRoot = options_.root;
    after_.keyQuality = options_.mood == 2 ? 0 : 1;
    after_.sunroomMood = options_.mood;
    after_.sunroomGuide = true;
    after_.loopEnabled = true;
    after_.loopStartBeats = 0;
    after_.loopEndBeats = options_.bars * 4;
    if (after_.markers.empty()) {
        const int sections = options_.bars == 8 ? 1 : 4;
        for (int i = 0; i < sections; ++i)
            after_.markers.push_back({i + 1, double(i * options_.bars * 4 / sections),
                                      sections == 1 ? "Loop" : sectionName(i),
                                      layers[static_cast<size_t>(i)].colour});
    }
    applyProject(after_);
    const auto song = compose(options_);
    for (size_t layer = 0; layer < layers.size(); ++layer) {
        if (song.phrases[layer].empty())
            continue;
        const auto id = tm.createTrack(layers[layer].name, TrackType::Audio);
        ids_.push_back(id);
        installSound(id, static_cast<int>(layer), options_);
        for (const auto& phrase : song.phrases[layer]) {
            const auto clip = cm.createMidiClipBeats(id, phrase.start, phrase.length);
            cm.setClipName(clip, juce::String(phrase.name) + " / " + layers[layer].name);
            cm.setClipColour(clip, juce::Colour(layers[layer].colour));
            for (const auto& n : phrase.notes) {
                MidiNote note;
                note.noteNumber = n.pitch;
                note.startBeat = n.beat;
                note.lengthBeats = n.length;
                note.velocity = n.velocity;
                cm.addMidiNote(clip, note);
            }
            if (const auto* c = cm.getClip(clip))
                clips_.push_back(*c);
        }
        if (const auto* t = tm.getTrack(id))
            tracks_.push_back(*t);
    }
    if (engine_)
        engine_->locate(0);
    captured_ = true;
}
void CreateJourneyCommand::undo() {
    if (engine_)
        engine_->stop();
    auto& cm = ClipManager::getInstance();
    ClipManager::BatchScope batch;
    for (const auto& clip : clips_)
        cm.deleteClip(clip.id);
    for (auto id : ids_)
        TrackManager::getInstance().deleteTrack(id);
    applyProject(before_);
}
juce::File soundLibrary() {
#if JUCE_MAC
    auto dir = juce::File::getSpecialLocation(juce::File::currentApplicationFile)
                   .getChildFile("Contents/Resources/Sunroom/Sounds");
#else
    auto dir = paths::executableDir().getChildFile("Sunroom/Sounds");
#endif
    if (dir.isDirectory())
        return dir;
    return juce::File(SUNROOM_SOURCE_DIR).getChildFile("resources/sunroom/Sounds");
}
}  // namespace magda::sunroom
