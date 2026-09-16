#include <cassert>
#include <iostream>
#include <limits>
#include <sstream>

#include "magda/daw/sunroom/MusicTheory.hpp"
using namespace magda::sunroom;
std::string fingerprint(const Journey& song) {
    std::ostringstream s;
    for (auto& layer : song.phrases)
        for (auto& p : layer)
            for (auto& n : p.notes)
                s << n.pitch << ':' << n.beat << ':' << n.velocity << ';';
    return s.str();
}
int main() {
    assert(pitchClass(-1) == 11 && pitchClass(14) == 2);
    assert(degreeNote(7, 2, 0) == 62 && degreeNote(-1, 2, 0) == 48);
    assert(inScale(59, 2, 0) && !inScale(58, 2, 0));  // B vs Bb defines D Dorian.
    assert(feeling(62, 2, 0).kind == Feeling::Home);
    assert(feeling(69, 2, 0).kind == Feeling::Anchor);
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
                        assert(phrase.start >= 0 && phrase.start + phrase.length <= bars * 4);
                        for (auto& n : phrase.notes) {
                            ++notes;
                            assert(n.pitch >= 0 && n.pitch <= 127 && n.velocity > 0 &&
                                   n.velocity <= 127);
                            assert(std::isfinite(n.beat) && std::isfinite(n.length) &&
                                   n.beat >= 0 && n.length > 0);
                            assert(n.beat + n.length <= phrase.length + .00001);
                            if (layers[layer].melodic)
                                assert(inScale(n.pitch, root, mood));
                        }
                    }
            }
    Options o;
    auto a = compose(o), b = compose(o);
    assert(fingerprint(a) == fingerprint(b));
    ++o.seed;
    assert(fingerprint(a) != fingerprint(compose(o)));
    o.enabled.fill(false);
    for (auto& layer : compose(o).phrases)
        assert(layer.empty());
    o.tempo = std::numeric_limits<double>::quiet_NaN();
    o.motion = INFINITY;
    o.root = -1;
    o.mood = 42;
    o.bars = -9;
    auto safe = sanitise(o);
    assert(safe.tempo == 84 && safe.motion == .5f && safe.root == 11 && safe.mood == 3 &&
           safe.bars == 8);
    for (auto& phrase : a.phrases[4])
        assert(phrase.start >= 32 && phrase.start < 96);  // calm intro/outro
    std::cout << journeys << " arrangements, " << notes
              << " notes, pitch/timing/scale/variation bounds passed.\n";
}
