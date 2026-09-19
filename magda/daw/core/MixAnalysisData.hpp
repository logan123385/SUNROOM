#pragma once

#include <array>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace magda {

/**
 * Whole-mix measurements and DAW-owned project context.
 *
 * This type deliberately has no dependency on the agent layer. Agents may
 * consume it, but DAW measurement and caching code must remain usable without
 * linking magda_agents.
 */
struct MixAnalysisData {
    /** One track's measurements. */
    struct Track {
        std::string name;
        std::string role;  // optional hint ("kick", "bass", "vocal", "bus", ...)
        float integratedLufs = -100.0f;
        float shortTermLufs = -100.0f;
        float samplePeakDb = -200.0f;
        float truePeakDb = -200.0f;  // oversampled dBTP; > 0 = real inter-sample clipping
        bool truePeakValid = false;  // false when true-peak wasn't measured
        float plr = 0.0f;            // peak - integrated (crest / dynamics, LU)
        float psr = 0.0f;            // peak - short-term (LU)
        float correlation = 1.0f;    // -1..1 (1 mono, 0 wide, <0 out of phase)
        float width = 0.0f;          // 0..1 side/(mid+side) energy
        // Spectral descriptors (0 / unset when the spectral layer wasn't run).
        float spectralCentroidHz = 0.0f;  // brightness: energy-weighted mean freq
        float spectralFlatness = 0.0f;    // 0 tonal .. 1 noisy
        float spectralRolloffHz = 0.0f;   // frequency below which 85% of energy sits
        // Macro-band energy in dB, ordered sub / low / low-mid / mid /
        // high-mid / high. Empty when the spectral layer wasn't run.
        inline static constexpr std::array<std::string_view, 6> tonalBandLabels = {
            "sub", "low", "low-mid", "mid", "high-mid", "high"};
        std::vector<float> tonalDb;
        // Effect inserts on this track, in order. Empty means no processing.
        std::vector<std::string> chain;
    };

    /** Two tracks competing in a frequency band. */
    struct MaskingPair {
        std::string a, b;
        float loHz = 0.0f, hiHz = 0.0f;
        float severity = 0.0f;  // 0..1, worst band in the range
    };

    /** One time slice of the mix for arrangement-level analysis. */
    struct Segment {
        std::string label;
        float startSec = 0.0f;
        float endSec = 0.0f;
        float integratedLufs = -100.0f;
        float spectralCentroidHz = 0.0f;
        float width = 0.0f;
        std::vector<float> tonalDb;
    };

    std::vector<Track> tracks;
    std::optional<Track> master;
    std::vector<MaskingPair> masking;
    std::vector<Segment> timeline;
    std::vector<Track> references;
    float bpm = 0.0f;
    std::string genre;
};

inline std::string formatFixed(float value, int digits) {
    const bool negative = value < 0.0f;
    float magnitude = negative ? -value : value;
    int scale = 1;
    for (int i = 0; i < digits; ++i)
        scale *= 10;
    const int scaled = static_cast<int>(magnitude * static_cast<float>(scale) + 0.5f);
    std::string text = std::to_string(scaled / scale);
    if (digits > 0) {
        text.push_back('.');
        auto fraction = std::to_string(scaled % scale);
        text.append(static_cast<size_t>(digits) - fraction.size(), '0');
        text += fraction;
    }
    return negative ? "-" + text : text;
}

/** Measured levels and collisions only. No mix-health score. */
inline std::string formatMixFindings(const MixAnalysisData& in) {
    std::string out = "LEVELS (" + std::to_string(in.tracks.size()) + " tracks)\n";
    out += "NAME            LUFS   PEAK\n";
    auto line = [&](const std::string& name, const MixAnalysisData::Track& track) {
        const auto shown = name.size() < 14 ? name : name.substr(0, 14);
        out += shown;
        if (shown.size() < 16)
            out.append(16 - shown.size(), ' ');
        out += formatFixed(track.integratedLufs, 1);
        out += "  ";
        out += formatFixed(track.samplePeakDb, 1);
        out += "\n";
    };
    for (const auto& track : in.tracks)
        line(track.name, track);
    if (in.master)
        line("[MASTER]", *in.master);
    out += "\nCOLLISIONS (" + std::to_string(in.masking.size()) + ")\n";
    if (in.masking.empty()) {
        out += "  none detected\n";
    } else {
        for (const auto& pair : in.masking) {
            out += "  " + pair.a + " vs " + pair.b + " ";
            out += formatFixed(pair.loHz, 0) + "-" + formatFixed(pair.hiHz, 0);
            out += " Hz " + formatFixed(pair.severity, 2) + "\n";
        }
    }
    return out;
}

}  // namespace magda
