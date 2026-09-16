#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>

#include "magda/daw/sunroom/MusicTheory.hpp"

using namespace magda::sunroom;

// Always-on checks so Release CTest builds still validate theory bounds.
#define REQUIRE(cond)                                                                              \
    do {                                                                                           \
        if (!(cond))                                                                               \
            throw std::runtime_error(std::string("theory_test failed: ") + #cond + " at " +        \
                                     __FILE__ + ":" + std::to_string(__LINE__));                   \
    } while (0)

std::string fingerprint(const Journey& song) {
    std::ostringstream s;
    for (auto& layer : song.phrases)
        for (auto& p : layer)
            for (auto& n : p.notes)
                s << n.pitch << ':' << n.beat << ':' << n.velocity << ';';
    return s.str();
}

int main() {
    try {
        REQUIRE(pitchClass(-1) == 11 && pitchClass(14) == 2);
        REQUIRE(degreeNote(7, 2, 0) == 62 && degreeNote(-1, 2, 0) == 48);
        REQUIRE(inScale(59, 2, 0) && !inScale(58, 2, 0));  // B vs Bb defines D Dorian.
        REQUIRE(feeling(62, 2, 0).kind == Feeling::Home);
        REQUIRE(feeling(69, 2, 0).kind == Feeling::Anchor);
        int journeys = 0, notes = 0;
        for (int mood = 0; mood < 4; ++mood)
            for (int root = 0; root < 12; ++root)
                for (int bars : {8, 32, 64}) {
                    Options o;
                    o.mood = mood;
                    o.root = root;
                    o.bars = bars;
                    auto song = compose(o);
                    ++journeys;
                    for (size_t layer = 0; layer < 7; ++layer)
                        for (auto& phrase : song.phrases[layer]) {
                            REQUIRE(phrase.start >= 0 &&
                                    phrase.start + phrase.length <= bars * 4);
                            for (auto& n : phrase.notes) {
                                ++notes;
                                REQUIRE(n.pitch >= 0 && n.pitch <= 127 && n.velocity > 0 &&
                                        n.velocity <= 127);
                                REQUIRE(std::isfinite(n.beat) && std::isfinite(n.length) &&
                                        n.beat >= 0 && n.length > 0);
                                REQUIRE(n.beat + n.length <= phrase.length + .00001);
                                if (layers[layer].melodic)
                                    REQUIRE(inScale(n.pitch, root, mood));
                            }
                        }
                }
        Options o;
        auto a = compose(o), b = compose(o);
        REQUIRE(fingerprint(a) == fingerprint(b));
        ++o.seed;
        REQUIRE(fingerprint(a) != fingerprint(compose(o)));
        o.enabled.fill(false);
        for (auto& layer : compose(o).phrases)
            REQUIRE(layer.empty());
        o.tempo = std::numeric_limits<double>::quiet_NaN();
        o.motion = INFINITY;
        o.root = -1;
        o.mood = 42;
        o.bars = -9;
        auto safe = sanitise(o);
        REQUIRE(safe.tempo == 84 && safe.motion == .5f && safe.root == 11 && safe.mood == 3 &&
                safe.bars == 8);
        for (auto& phrase : a.phrases[4])
            REQUIRE(phrase.start >= 32 && phrase.start < 96);  // calm intro/outro
        std::cout << journeys << " arrangements, " << notes
                  << " notes, pitch/timing/scale/variation bounds passed.\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
